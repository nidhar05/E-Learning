import subprocess


def extract_audio(video_path):
    audio_path = video_path.rsplit(".", 1)[0] + ".mp3"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "mp3",
        "-y",
        audio_path
    ]

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return audio_path