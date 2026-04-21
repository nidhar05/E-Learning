import threading

from django.db.models.signals import post_save
from django.dispatch import receiver

from videos.models import Video

from .content_processor import VideoContentProcessor
from .subtitle_utils import safe_log


def run_processing(video):
    try:
        safe_log(f"Processing video in background: {video.id}")
        VideoContentProcessor.process_video(video)
    except Exception as e:
        safe_log(f"Error processing video {video.id}: {e}")


@receiver(post_save, sender=Video)
def process_video_async(sender, instance, created, **kwargs):
    if created:
        threading.Thread(target=run_processing, args=(instance,), daemon=True).start()
