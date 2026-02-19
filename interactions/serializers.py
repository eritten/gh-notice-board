from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Like, Dislike, Review, Bookmark
from news.models import NewsArticle
from events.models import Event
from opportunities.models import Opportunity
from diaspora.models import DiasporaPost


BOOKMARK_TYPE_MODEL_MAP = {
    'news': NewsArticle,
    'event': Event,
    'opportunity': Opportunity,
    'diaspora': DiasporaPost,
}

BOOKMARK_TYPE_ALIASES = {
    'news': 'news',
    'article': 'news',
    'articles': 'news',
    'event': 'event',
    'events': 'event',
    'opportunity': 'opportunity',
    'opportunities': 'opportunity',
    'diaspora': 'diaspora',
    'diaspora_post': 'diaspora',
    'diaspora_posts': 'diaspora',
    'post': 'diaspora',
    'posts': 'diaspora',
}


def normalize_bookmark_type(value):
    if value is None:
        return None
    return BOOKMARK_TYPE_ALIASES.get(str(value).strip().lower())


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
    type = serializers.SerializerMethodField()
    item = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = [
            'id', 'user', 'user_username', 'content_type', 'object_id',
            'content_type_name', 'type', 'item', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

    def get_content_type_name(self, obj):
        return obj.content_type.model

    def get_type(self, obj):
        model = obj.content_type.model
        for bookmark_type, mapped_model in BOOKMARK_TYPE_MODEL_MAP.items():
            if model == mapped_model._meta.model_name:
                return bookmark_type
        return model

    def get_item(self, obj):
        content_object = obj.content_object
        if not content_object:
            return None

        return {
            'id': str(content_object.pk),
            'slug': getattr(content_object, 'slug', None),
            'title': getattr(content_object, 'title', None),
            'summary': getattr(content_object, 'summary', None),
        }


class BookmarkCreateSerializer(serializers.Serializer):
    """Serializer for creating bookmarks with a normalized content type."""
    type = serializers.CharField()
    object_id = serializers.CharField()

    def validate_type(self, value):
        normalized_type = normalize_bookmark_type(value)
        if not normalized_type:
            allowed_types = ', '.join(sorted(BOOKMARK_TYPE_MODEL_MAP.keys()))
            raise serializers.ValidationError(
                f"Unsupported type '{value}'. Use one of: {allowed_types}."
            )
        return normalized_type

    def validate(self, attrs):
        model_class = BOOKMARK_TYPE_MODEL_MAP[attrs['type']]
        object_id = attrs['object_id']

        if not model_class.objects.filter(pk=object_id).exists():
            raise serializers.ValidationError({
                'object_id': f"{attrs['type']} item with id '{object_id}' was not found."
            })

        attrs['content_type'] = ContentType.objects.get_for_model(model_class)
        return attrs


class BookmarkDeleteSerializer(BookmarkCreateSerializer):
    """Serializer for deleting bookmarks."""
    pass


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
