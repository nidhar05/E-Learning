import subprocess


def extract_audio(video_path, start_seconds=None, duration_seconds=None, suffix=""):
    audio_path = video_path.rsplit(".", 1)[0] + f"{suffix}.wav"

    command = ["ffmpeg", "-nostdin"]
    if start_seconds is not None:
        command.extend(["-ss", str(start_seconds)])
    command.extend(["-i", video_path])
    if duration_seconds is not None:
        command.extend(["-t", str(duration_seconds)])
    command.extend([
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        "-y",
        audio_path
    ])

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_output = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffmpeg audio extraction failed: {error_output[:500]}")

    return audio_path


def get_media_duration(video_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_output = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffprobe duration check failed: {error_output[:500]}")

    output = result.stdout.decode("utf-8", errors="ignore").strip()
    if not output:
        raise RuntimeError("ffprobe did not return media duration")

    return float(output)
