import os
import warnings

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

from .utils.audio_utils import extract_audio


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

    @staticmethod
    def get_backend():
        if WhisperModel is not None:
            return "faster_whisper"
        if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
            return "openai"
        return None

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
    def transcribe_with_faster_whisper(video_path):
        model = AudioTranscriber.get_model()
        task = AudioTranscriber.get_whisper_task()
        segments, info = model.transcribe(
            video_path,
            task=task,
            beam_size=5,
            vad_filter=True,
            word_timestamps=False,
        )
        segments = list(segments)
        safe_log(
            f"faster-whisper complete: task={task}, language={getattr(info, 'language', 'unknown')}, segments={len(segments)}"
        )
        return build_srt_from_segments(segments)

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

            backend = AudioTranscriber.get_backend()
            if backend is None:
                safe_log("No transcription backend available")
                return None

            safe_log(f"Using transcription backend: {backend}")

            if backend == "faster_whisper":
                return AudioTranscriber.transcribe_with_faster_whisper(video_path)

            audio_path = extract_audio(video_path)
            safe_log(f"Audio extracted: {audio_path}")
            transcript = AudioTranscriber.transcribe_with_openai(audio_path)
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
