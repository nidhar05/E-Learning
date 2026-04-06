from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    sender = serializers.StringRelatedField()
    target_url = serializers.SerializerMethodField()

    class Meta:

        model = Notification

        fields = [
            "id",
            "sender",
            "notification_type",
            "message",
            "course",
            "video",
            "comment",
            "target_url",
            "is_read",
            "created_at"
        ]

    def get_target_url(self, obj):
        if obj.comment_id and obj.course_id:
            if obj.notification_type == Notification.TYPE_COMMENT_REPLY and obj.comment.parent_id:
                return (
                    f"/course/{obj.course_id}"
                    f"?comment={obj.comment.parent_id}&reply={obj.comment_id}"
                    f"#reply-{obj.comment_id}"
                )

            return f"/course/{obj.course_id}?comment={obj.comment_id}#comment-{obj.comment_id}"

        if obj.video_id and obj.course_id:
            return f"/course/{obj.course_id}/watch/{obj.video_id}"

        if obj.course_id:
            return f"/course/{obj.course_id}"

        return None
