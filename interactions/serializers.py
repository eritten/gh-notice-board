from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Like, Dislike, Review, Bookmark


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for likes"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['id', 'user', 'user_username', 'content_type', 'object_id',
                  'content_type_name', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_content_type_name(self, obj):
        return obj.content_type.model


class DislikeSerializer(serializers.ModelSerializer):
    """Serializer for dislikes"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Dislike
        fields = ['id', 'user', 'user_username', 'content_type', 'object_id',
                  'content_type_name', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_content_type_name(self, obj):
        return obj.content_type.model


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_id', 'user_username', 'content_type', 'object_id',
                  'content_type_name', 'rating', 'title', 'comment', 'is_approved',
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'is_approved', 'created_at', 'updated_at']

    def get_content_type_name(self, obj):
        return obj.content_type.model

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class BookmarkSerializer(serializers.ModelSerializer):
    """Serializer for bookmarks"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'user_username', 'content_type', 'object_id',
                  'content_type_name', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_content_type_name(self, obj):
        return obj.content_type.model


class InteractionStatsSerializer(serializers.Serializer):
    """Serializer for interaction statistics"""
    likes_count = serializers.IntegerField()
    dislikes_count = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    average_rating = serializers.FloatField()
    user_liked = serializers.BooleanField()
    user_disliked = serializers.BooleanField()
    user_bookmarked = serializers.BooleanField()
    user_review = ReviewSerializer(allow_null=True)
