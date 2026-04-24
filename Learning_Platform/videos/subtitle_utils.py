import os
import re
import warnings
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
        text = (segment.text or "").strip()
        if not text:
            continue

        caption_blocks = split_text_for_captions(text)
        if not caption_blocks:
            continue

        total_duration = max(segment.end - segment.start, 0.8)
        total_chars = sum(len(block.replace("\n", " ").strip()) for block in caption_blocks) or 1
        block_start = segment.start

        for block_position, block in enumerate(caption_blocks):
            block_chars = len(block.replace("\n", " ").strip())
            duration_share = total_duration * (block_chars / total_chars)
            remaining_blocks = len(caption_blocks) - block_position - 1
            min_remaining = remaining_blocks * 0.8
            max_end = segment.end - min_remaining
            block_end = min(block_start + max(duration_share, 0.8), max_end)

            if remaining_blocks == 0:
                block_end = segment.end

            srt_lines.append(str(cue_index))
            srt_lines.append(
                f"{format_srt_timestamp(block_start)} --> {format_srt_timestamp(block_end)}"
            )
            srt_lines.append(block)
            srt_lines.append("")

            cue_index += 1
            block_start = block_end

    return "\n".join(srt_lines)


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
            word_timestamps=False,
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
            safe_log(
                f"faster-whisper complete: task={task}, language={getattr(info, 'language', 'unknown')}, segments={len(segments)}"
            )
            return build_srt_from_segments(segments)
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
        return build_srt_from_segments(combined_segments)

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
                transcript_text = SubtitleParser.parse_srt_file(transcript) if transcript else ""
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

    lines = ["WEBVTT", ""]
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
