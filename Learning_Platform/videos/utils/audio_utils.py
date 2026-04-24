import subprocess


def _run_ffprobe_duration(video_path, stream_selector=None):
    command = [
        "ffprobe",
        "-v", "error",
    ]
    if stream_selector:
        command.extend(["-select_streams", stream_selector])
    command.extend([
        "-show_entries",
        "stream=duration" if stream_selector else "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ])

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        return None

    for raw_line in result.stdout.decode("utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.upper() == "N/A":
            continue
        try:
            duration = float(line)
        except ValueError:
            continue
        if duration > 0:
            return duration

    return None


def get_video_stream_duration(video_path):
    return _run_ffprobe_duration(video_path, "v:0")


def extract_audio(video_path, start_seconds=None, duration_seconds=None, suffix=""):
    audio_path = video_path.rsplit(".", 1)[0] + f"{suffix}.wav"
    capped_duration = duration_seconds
    if capped_duration is None:
        video_duration = get_video_stream_duration(video_path)
        if video_duration:
            capped_duration = video_duration

    command = ["ffmpeg", "-nostdin"]
    if start_seconds is not None:
        command.extend(["-ss", str(start_seconds)])
    command.extend(["-i", video_path])
    if capped_duration is not None:
        command.extend(["-t", str(capped_duration)])
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
    duration = get_video_stream_duration(video_path) or _run_ffprobe_duration(video_path)
    if not duration:
        raise RuntimeError("ffprobe did not return media duration")

    return duration
