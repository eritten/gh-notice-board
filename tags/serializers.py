from rest_framework import serializers
from .models import Category, Tag, SubTag, UserSubscription, PushSubscription, UserInterest


class SubTagSerializer(serializers.ModelSerializer):
    """Serializer for SubTags"""
    class Meta:
        model = SubTag
        fields = ['id', 'name', 'slug', 'description', 'parent_tag',
                  'usage_count', 'is_active', 'created_at']
        read_only_fields = ['slug', 'usage_count', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tags"""
    subtags = SubTagSerializer(many=True, read_only=True)
    subtag_count = serializers.IntegerField(source='subtags.count', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'description', 'category', 'category_name',
                  'usage_count', 'is_active', 'created_at', 'subtags', 'subtag_count',
                  'is_subscribed']
        read_only_fields = ['slug', 'usage_count', 'created_at']

    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this tag"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserSubscription.objects.filter(
                user=request.user,
                tag=obj
            ).exists()
        return False


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Categories"""
    tags = TagSerializer(many=True, read_only=True)
    tag_count = serializers.IntegerField(source='tags.count', read_only=True)
    subscriber_count = serializers.IntegerField(source='subscribers.count', read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'color', 'order',
                  'is_active', 'created_at', 'tags', 'tag_count', 'subscriber_count',
                  'is_subscribed']
        read_only_fields = ['slug', 'created_at']

    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this category"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserSubscription.objects.filter(
                user=request.user,
                category=obj
            ).exists()
        return False


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for User Subscriptions"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    subtag_name = serializers.CharField(source='subtag.name', read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'category', 'category_name', 'tag', 'tag_name',
                  'subtag', 'subtag_name', 'push_notifications', 'email_notifications',
                  'notification_frequency', 'created_at']
        read_only_fields = ['user', 'created_at']

    def validate(self, data):
        """Ensure at least one subscription target is provided"""
        if not any([data.get('category'), data.get('tag'), data.get('subtag')]):
            raise serializers.ValidationError(
                "Must subscribe to at least one: category, tag, or subtag"
            )
        return data


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Push Subscriptions"""
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'p256dh', 'auth', 'device_name',
                  'is_active', 'created_at']
        read_only_fields = ['user', 'created_at']


class UserInterestSerializer(serializers.ModelSerializer):
    """Serializer for User Interests"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    tag_name = serializers.CharField(source='tag.name', read_only=True)

    class Meta:
        model = UserInterest
        fields = ['id', 'category', 'category_name', 'tag', 'tag_name',
                  'score', 'view_count', 'like_count', 'share_count',
                  'time_spent', 'updated_at']
        read_only_fields = ['score', 'updated_at']


class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics"""
    total_subscriptions = serializers.IntegerField()
    category_subscriptions = serializers.IntegerField()
    tag_subscriptions = serializers.IntegerField()
    subtag_subscriptions = serializers.IntegerField()
    push_enabled_count = serializers.IntegerField()
    email_enabled_count = serializers.IntegerField()
