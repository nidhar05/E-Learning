from rest_framework import serializers
from .models import Comment

class ReplySerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()

    class Meta:
        model = Comment

        fields = [
            "id",
            "user",
            "text",
            "created_at"
        ]
        
class CommentSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()

    replies = ReplySerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Comment

        fields = [
            "id",
            "user",
            "course",
            "text",
            "parent",
            "created_at",
            "replies"
        ]