from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    sender = serializers.StringRelatedField()

    class Meta:

        model = Notification

        fields = [
            "id",
            "sender",
            "message",
            "is_read",
            "created_at"
        ]