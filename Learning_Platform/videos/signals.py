import threading

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from videos.models import Video

from .content_processor import VideoContentProcessor
from .subtitle_utils import safe_log


def run_processing(video_id):
    try:
        video = Video.objects.get(pk=video_id)
        safe_log(f"Processing video in background: {video.id}")
        VideoContentProcessor.process_video(video)
    except Exception as e:
        safe_log(f"Error processing video {video_id}: {e}")


def schedule_video_processing(video_id):
    transaction.on_commit(
        lambda: threading.Thread(
            target=run_processing,
            args=(video_id,),
            daemon=True,
        ).start()
    )


@receiver(post_save, sender=Video)
def process_video_async(sender, instance, created, **kwargs):
    if created:
        schedule_video_processing(instance.id)
