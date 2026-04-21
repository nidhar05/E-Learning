import os

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


def build_srt_from_segments(segments):
    srt_lines = []

    for index, segment in enumerate(segments, start=1):
        text = (segment.text or "").strip()
        if not text:
            continue

        srt_lines.append(str(index))
        srt_lines.append(
            f"{format_srt_timestamp(segment.start)} --> {format_srt_timestamp(segment.end)}"
        )
        srt_lines.append(text)
        srt_lines.append("")

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
    def transcribe_with_faster_whisper(video_path):
        model = AudioTranscriber.get_model()
        segments, info = model.transcribe(
            video_path,
            beam_size=5,
            vad_filter=True,
            word_timestamps=False,
        )
        segments = list(segments)
        safe_log(
            f"faster-whisper transcription complete: language={getattr(info, 'language', 'unknown')}, segments={len(segments)}"
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
