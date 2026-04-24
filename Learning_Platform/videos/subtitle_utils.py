import os
import re
import warnings
from textwrap import wrap
from types import SimpleNamespace

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .utils.audio_utils import extract_audio, get_media_duration


warnings.filterwarnings(
    "ignore",
    message=r".*unauthenticated requests to the HF Hub.*",
)


def safe_log(message):
    print(message.encode("ascii", errors="ignore").decode("ascii"))


def format_srt_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))

    if milliseconds == 1000:
        secs += 1
        milliseconds = 0

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def parse_srt_timestamp(timestamp):
    cleaned = (timestamp or "").strip().replace(".", ",")
    hours, minutes, seconds = cleaned.split(":")
    secs, milliseconds = seconds.split(",")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(secs)
        + int(milliseconds) / 1000
    )


def shift_srt_timestamps(srt_content, offset_seconds):
    shifted_lines = []

    for line in (srt_content or "").splitlines():
        if "-->" not in line:
            shifted_lines.append(line)
            continue

        start_raw, end_raw = [part.strip() for part in line.split("-->")]
        start_shifted = format_srt_timestamp(parse_srt_timestamp(start_raw) + offset_seconds)
        end_shifted = format_srt_timestamp(parse_srt_timestamp(end_raw) + offset_seconds)
        shifted_lines.append(f"{start_shifted} --> {end_shifted}")

    return "\n".join(shifted_lines)


def renumber_srt_cues(srt_content):
    blocks = re.split(r"\r?\n\r?\n+", (srt_content or "").strip())
    normalized_blocks = []

    for index, block in enumerate(blocks, start=1):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        if lines[0].strip().isdigit():
            lines = lines[1:]

        normalized_blocks.append("\n".join([str(index)] + lines))

    if not normalized_blocks:
        return ""

    return "\n\n".join(normalized_blocks) + "\n"


def split_text_for_captions(text, max_line_chars=38, max_lines=2):
    words = text.split()
    if not words:
        return []

    caption_blocks = []
    current_block = []
    current_line = ""
    current_line_count = 1

    for word in words:
        candidate = f"{current_line} {word}".strip()
        if len(candidate) <= max_line_chars:
            current_line = candidate
            continue

        if current_line_count < max_lines:
            current_block.append(current_line)
            current_line = word
            current_line_count += 1
            continue

        current_block.append(current_line)
        caption_blocks.append("\n".join(line for line in current_block if line.strip()))
        current_block = []
        current_line = word
        current_line_count = 1

    if current_line:
        current_block.append(current_line)
    if current_block:
        caption_blocks.append("\n".join(line for line in current_block if line.strip()))

    return caption_blocks


def build_srt_from_segments(segments):
    srt_lines = []
    cue_index = 1

    for segment in segments:
        words = [
            word
            for word in getattr(segment, "words", []) or []
            if getattr(word, "word", "").strip()
            and getattr(word, "start", None) is not None
            and getattr(word, "end", None) is not None
        ]
        if words:
            for cue in build_srt_cues_from_words(words):
                srt_lines.append(str(cue_index))
                srt_lines.append(
                    f"{format_srt_timestamp(cue.start)} --> {format_srt_timestamp(cue.end)}"
                )
                srt_lines.append(cue.text)
                srt_lines.append("")
                cue_index += 1
            continue

        text = (segment.text or "").strip()
        if not text:
            continue

        cue_start = float(getattr(segment, "start", 0) or 0)
        cue_end = float(getattr(segment, "end", cue_start + 2.0) or cue_start + 2.0)
        if cue_end <= cue_start:
            cue_end = cue_start + 1.0

        srt_lines.append(str(cue_index))
        srt_lines.append(f"{format_srt_timestamp(cue_start)} --> {format_srt_timestamp(cue_end)}")
        srt_lines.append(format_caption_text(text))
        srt_lines.append("")
        cue_index += 1

    return "\n".join(srt_lines)


def format_caption_text(text, max_line_chars=38):
    words = " ".join((text or "").split())
    if not words:
        return ""

    lines = wrap(words, width=max_line_chars, break_long_words=False, break_on_hyphens=False)
    return "\n".join(lines[:2]) if lines else words


def build_srt_cues_from_words(words, max_chars=64, max_duration=3.5, max_gap=0.65):
    cues = []
    current_words = []
    current_start = None
    previous_end = None

    def flush():
        nonlocal current_words, current_start, previous_end
        if not current_words or current_start is None or previous_end is None:
            current_words = []
            current_start = None
            previous_end = None
            return

        cue_text = format_caption_text(" ".join(current_words))
        cue_end = max(float(previous_end), float(current_start) + 0.45)
        cues.append(SimpleNamespace(start=float(current_start), end=cue_end, text=cue_text))
        current_words = []
        current_start = None
        previous_end = None

    for word in words:
        word_text = getattr(word, "word", "").strip()
        word_start = float(getattr(word, "start", 0) or 0)
        word_end = float(getattr(word, "end", word_start + 0.45) or word_start + 0.45)
        if not word_text:
            continue

        candidate_text = " ".join(current_words + [word_text])
        cue_duration = word_end - (current_start if current_start is not None else word_start)
        gap = (word_start - previous_end) if previous_end is not None else 0

        if current_words and (
            len(candidate_text) > max_chars
            or cue_duration > max_duration
            or gap > max_gap
        ):
            flush()

        if current_start is None:
            current_start = word_start
        current_words.append(word_text)
        previous_end = word_end

    flush()
    return cues


class AudioTranscriber:
    _whisper_model = None
    LONG_VIDEO_THRESHOLD_SECONDS = 1800

    @staticmethod
    def get_backend():
        if WhisperModel is not None:
            return "faster_whisper"
        if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
            return "openai"
        return None

    @staticmethod
    def has_openai_fallback():
        return OpenAI is not None and bool(os.getenv("OPENAI_API_KEY"))

    @staticmethod
    def should_prefer_openai_for_video(duration_seconds):
        return (
            AudioTranscriber.has_openai_fallback()
            and duration_seconds is not None
            and duration_seconds >= AudioTranscriber.LONG_VIDEO_THRESHOLD_SECONDS
        )

    @staticmethod
    def is_available():
        return AudioTranscriber.get_backend() is not None

    @staticmethod
    def get_model():
        if AudioTranscriber._whisper_model is None:
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            device = os.getenv("WHISPER_DEVICE", "cpu")
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

            safe_log(
                f"Loading faster-whisper model size={model_size}, device={device}, compute_type={compute_type}"
            )
            AudioTranscriber._whisper_model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )

        return AudioTranscriber._whisper_model

    @staticmethod
    def get_whisper_task():
        return getattr(settings, "WHISPER_TASK", "translate")

    @staticmethod
    def _transcribe_source_with_faster_whisper(source_path, task):
        model = AudioTranscriber.get_model()
        segments, info = model.transcribe(
            source_path,
            task=task,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
        )
        segments = list(segments)
        return segments, info

    @staticmethod
    def transcribe_with_faster_whisper(video_path):
        task = AudioTranscriber.get_whisper_task()
        audio_path = None

        try:
            audio_path = extract_audio(video_path)
            source_path = audio_path if os.path.exists(audio_path) else video_path
            safe_log(f"Transcribing source: {source_path}")
            segments, info = AudioTranscriber._transcribe_source_with_faster_whisper(
                source_path,
                task,
            )
            detected_language = getattr(info, "language", None)
            safe_log(
                f"faster-whisper complete: task={task}, language={detected_language or 'unknown'}, segments={len(segments)}"
            )
            return SimpleNamespace(
                text=build_srt_from_segments(segments),
                language=detected_language,
            )
        except Exception as exc:
            if "Unable to allocate" not in str(exc):
                raise

            safe_log("Full-audio transcription ran out of memory; retrying in chunks")
            return AudioTranscriber.transcribe_with_faster_whisper_in_chunks(video_path, task=task)
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    safe_log(f"Could not remove temporary audio file: {audio_path}")

    @staticmethod
    def transcribe_with_faster_whisper_in_chunks(video_path, task=None, chunk_seconds=600):
        task = task or AudioTranscriber.get_whisper_task()
        total_duration = get_media_duration(video_path)
        safe_log(f"Chunked transcription start: duration={total_duration:.2f}s, chunk_seconds={chunk_seconds}")
        combined_segments = []
        detected_language = "unknown"
        chunk_index = 0
        current_start = 0.0

        while current_start < total_duration:
            current_duration = min(chunk_seconds, max(total_duration - current_start, 0))
            if current_duration <= 0:
                break

            chunk_suffix = f"_chunk_{chunk_index:03d}"
            chunk_audio_path = None
            try:
                chunk_audio_path = extract_audio(
                    video_path,
                    start_seconds=current_start,
                    duration_seconds=current_duration,
                    suffix=chunk_suffix,
                )
                safe_log(
                    f"Transcribing chunk {chunk_index + 1}: start={current_start:.2f}s duration={current_duration:.2f}s"
                )
                segments, info = AudioTranscriber._transcribe_source_with_faster_whisper(
                    chunk_audio_path,
                    task,
                )
                detected_language = getattr(info, "language", detected_language)

                for segment in segments:
                    combined_segments.append(
                        SimpleNamespace(
                            start=segment.start + current_start,
                            end=segment.end + current_start,
                            text=segment.text,
                            words=[
                                SimpleNamespace(
                                    start=word.start + current_start,
                                    end=word.end + current_start,
                                    word=word.word,
                                )
                                for word in getattr(segment, "words", []) or []
                            ],
                        )
                    )
            finally:
                if chunk_audio_path and os.path.exists(chunk_audio_path):
                    try:
                        os.remove(chunk_audio_path)
                    except OSError:
                        safe_log(f"Could not remove chunk audio file: {chunk_audio_path}")

            current_start += current_duration
            chunk_index += 1

        safe_log(
            f"Chunked faster-whisper complete: task={task}, language={detected_language}, segments={len(combined_segments)}"
        )
        return SimpleNamespace(
            text=build_srt_from_segments(combined_segments),
            language=None if detected_language == "unknown" else detected_language,
        )

    @staticmethod
    def transcribe_with_openai(audio_path):
        if OpenAI is None:
            return None

        client = OpenAI()
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="gpt-4o-transcribe",
                response_format="srt",
            )

        if hasattr(transcript, "text"):
            return transcript.text

        return transcript

    @staticmethod
    def transcribe_with_openai_in_chunks(video_path, chunk_seconds=600):
        if OpenAI is None:
            return None

        total_duration = get_media_duration(video_path)
        safe_log(
            f"Chunked OpenAI transcription start: duration={total_duration:.2f}s, chunk_seconds={chunk_seconds}"
        )
        chunk_outputs = []
        current_start = 0.0
        chunk_index = 0

        while current_start < total_duration:
            current_duration = min(chunk_seconds, max(total_duration - current_start, 0))
            if current_duration <= 0:
                break

            chunk_audio_path = None
            try:
                chunk_suffix = f"_chunk_{chunk_index:03d}"
                chunk_audio_path = extract_audio(
                    video_path,
                    start_seconds=current_start,
                    duration_seconds=current_duration,
                    suffix=chunk_suffix,
                )
                safe_log(
                    f"OpenAI transcribing chunk {chunk_index + 1}: start={current_start:.2f}s duration={current_duration:.2f}s"
                )
                chunk_srt = AudioTranscriber.transcribe_with_openai(chunk_audio_path)
                if chunk_srt:
                    if hasattr(chunk_srt, "text"):
                        chunk_srt = chunk_srt.text
                    chunk_outputs.append(shift_srt_timestamps(chunk_srt, current_start))
            finally:
                if chunk_audio_path and os.path.exists(chunk_audio_path):
                    try:
                        os.remove(chunk_audio_path)
                    except OSError:
                        safe_log(f"Could not remove OpenAI chunk audio file: {chunk_audio_path}")

            current_start += current_duration
            chunk_index += 1

        combined = renumber_srt_cues("\n\n".join(part for part in chunk_outputs if part))
        safe_log(
            f"Chunked OpenAI transcription complete: chunks={chunk_index}, has_output={bool(combined)}"
        )
        return combined or None

    @staticmethod
    def transcribe_video(video):
        try:
            video_file = video.original_file or video.processed_file
            if not video_file:
                safe_log("No video file found")
                return None

            video_path = os.path.join(settings.MEDIA_ROOT, video_file.name)
            if not os.path.exists(video_path):
                safe_log(f"Video path not found: {video_path}")
                return None

            total_duration = get_media_duration(video_path)
            backend = AudioTranscriber.get_backend()
            if backend is None:
                safe_log("No transcription backend available")
                return None

            if AudioTranscriber.should_prefer_openai_for_video(total_duration):
                safe_log(
                    f"Preferring chunked OpenAI transcription for long video ({total_duration:.2f}s)"
                )
                try:
                    transcript = AudioTranscriber.transcribe_with_openai_in_chunks(video_path)
                    if transcript:
                        return transcript
                    safe_log("Chunked OpenAI transcription returned no output; falling back to local backend")
                except Exception as exc:
                    safe_log(f"Chunked OpenAI transcription failed: {exc}")
                    safe_log("Falling back to local transcription backend")

            safe_log(f"Using transcription backend: {backend}")

            if backend == "faster_whisper":
                if total_duration >= 900:
                    safe_log(
                        f"Using chunked faster-whisper for long video ({total_duration:.2f}s)"
                    )
                    transcript = AudioTranscriber.transcribe_with_faster_whisper_in_chunks(video_path)
                else:
                    transcript = AudioTranscriber.transcribe_with_faster_whisper(video_path)
                transcript_content = transcript.text if hasattr(transcript, "text") else transcript
                transcript_text = SubtitleParser.parse_srt_file(transcript_content) if transcript_content else ""
                if transcript_text.strip():
                    return transcript

                safe_log("faster-whisper returned no transcript text")
                if AudioTranscriber.has_openai_fallback():
                    safe_log("Retrying transcription with chunked OpenAI fallback")
                    return AudioTranscriber.transcribe_with_openai_in_chunks(video_path)
                return None

            audio_path = None
            try:
                if total_duration > 600:
                    transcript = AudioTranscriber.transcribe_with_openai_in_chunks(video_path)
                else:
                    audio_path = extract_audio(video_path)
                    safe_log(f"Audio extracted: {audio_path}")
                    transcript = AudioTranscriber.transcribe_with_openai(audio_path)
            finally:
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        safe_log(f"Could not remove temporary audio file: {audio_path}")

            safe_log("OpenAI transcription success")
            return transcript
        except Exception as e:
            safe_log(f"Transcription error: {e}")
            return None


def convert_srt_to_vtt(srt_content):
    lines = srt_content.splitlines()
    vtt = ["WEBVTT", ""]

    for line in lines:
        if "-->" in line:
            line = line.replace(",", ".")
        vtt.append(line)

    return "\n".join(vtt)


def subtitle_file_has_synthetic_timing(file_obj):
    file_content = file_obj.read()
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8", errors="ignore")

    if "X-TIMING-SOURCE: plain-text-estimate" in file_content:
        return True

    cue_durations = []
    for line in file_content.splitlines():
        if "-->" not in line:
            continue

        try:
            start_raw, end_raw = [part.strip() for part in line.split("-->", 1)]
            cue_durations.append(
                round(parse_srt_timestamp(end_raw) - parse_srt_timestamp(start_raw), 3)
            )
        except (TypeError, ValueError):
            continue

    if len(cue_durations) < 6:
        return False

    six_second_cues = sum(1 for duration in cue_durations if abs(duration - 6.0) <= 0.05)
    return six_second_cues / len(cue_durations) >= 0.8


class SubtitleParser:
    @staticmethod
    def parse_srt_file(file_content):
        if isinstance(file_content, bytes):
            file_content = file_content.decode("utf-8", errors="ignore")

        lines = file_content.splitlines()
        subtitles = []

        for line in lines:
            line = line.strip()
            if not line or line.isdigit() or "-->" in line:
                continue
            subtitles.append(line)

        return " ".join(subtitles)

    @staticmethod
    def extract_text_from_subtitle_file(file_obj):
        file_content = file_obj.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode("utf-8", errors="ignore")

        lines = file_content.splitlines()
        subtitles = []

        for line in lines:
            line = line.strip()
            if not line or line.upper() == "WEBVTT" or line.isdigit() or "-->" in line:
                continue
            subtitles.append(line)

        return " ".join(subtitles)


def save_vtt_file(video, vtt_content):
    filename = f"subtitles/video_{video.id}_subtitles.vtt"

    if default_storage.exists(filename):
        default_storage.delete(filename)

    return default_storage.save(
        filename,
        ContentFile(vtt_content.encode("utf-8")),
    )


def format_vtt_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))

    if milliseconds == 1000:
        secs += 1
        milliseconds = 0

    return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"


def build_vtt_from_plain_text(text, segment_seconds=4.0):
    cleaned_text = " ".join((text or "").split())
    if not cleaned_text:
        return "WEBVTT\n"

    caption_blocks = split_text_for_captions(cleaned_text, max_line_chars=42, max_lines=2)
    if not caption_blocks:
        return "WEBVTT\n"

    lines = ["WEBVTT", "NOTE X-TIMING-SOURCE: plain-text-estimate", ""]
    current_start = 0.0

    for index, block in enumerate(caption_blocks, start=1):
        block_words = max(len(block.replace("\n", " ").split()), 1)
        block_duration = max(segment_seconds, min(6.0, block_words * 0.55))
        current_end = current_start + block_duration

        lines.append(str(index))
        lines.append(f"{format_vtt_timestamp(current_start)} --> {format_vtt_timestamp(current_end)}")
        lines.append(block)
        lines.append("")

        current_start = current_end

    return "\n".join(lines)
