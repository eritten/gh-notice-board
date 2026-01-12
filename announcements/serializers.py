from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    Announcement, AnnouncementImage, AnnouncementAcknowledgment,
    AnnouncementTranslation, AnnouncementAlert
)
from authentication.serializers import UserMinimalSerializer
from tags.serializers import TagSerializer, CategorySerializer
from interactions.models import Share, View

User = get_user_model()


class AnnouncementImageSerializer(serializers.ModelSerializer):
    """Serializer for announcement gallery images"""

    class Meta:
        model = AnnouncementImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class AnnouncementTranslationSerializer(serializers.ModelSerializer):
    """Serializer for announcement translations"""
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    verified_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = AnnouncementTranslation
        fields = [
            'id', 'language', 'language_display', 'title', 'summary', 'content',
            'is_machine_translated', 'verified_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for announcement lists"""
    posted_by = UserMinimalSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Display fields
    announcement_type_display = serializers.CharField(source='get_announcement_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)

    # Status and engagement
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    requires_action = serializers.BooleanField(read_only=True)
    action_overdue = serializers.BooleanField(read_only=True)
    user_acknowledged = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image',
            'announcement_type', 'announcement_type_display',
            'category', 'tags', 'posted_by',
            'source_organization', 'organization_logo', 'organization_verified',
            'reference_number', 'target_audience', 'target_audience_display',
            'is_national', 'regions', 'districts',
            'priority', 'priority_display', 'is_emergency', 'is_pinned', 'is_featured',
            'expires_at', 'days_until_expiry', 'is_active', 'is_expired',
            'action_required', 'action_deadline', 'requires_action', 'action_overdue',
            'requires_acknowledgment', 'user_acknowledged',
            'views_count', 'shares_count', 'acknowledgments_count',
            'status', 'created_at', 'published_at'
        ]

    def get_user_acknowledged(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.requires_acknowledgment:
            return AnnouncementAcknowledgment.objects.filter(
                announcement=obj,
                user=request.user
            ).exists()
        return False


class AnnouncementDetailSerializer(AnnouncementListSerializer):
    """Detailed serializer for announcement view"""
    approved_by = UserMinimalSerializer(read_only=True)
    gallery_images = AnnouncementImageSerializer(many=True, read_only=True)
    translations = AnnouncementTranslationSerializer(many=True, read_only=True)

    # Related announcements
    related_announcements = serializers.SerializerMethodField()
    acknowledgment_details = serializers.SerializerMethodField()

    class Meta(AnnouncementListSerializer.Meta):
        fields = AnnouncementListSerializer.Meta.fields + [
            'content', 'location_details',
            'contact_person', 'contact_email', 'contact_phone',
            'contact_address', 'website_url', 'whatsapp_number',
            'document', 'document_title', 'video_url',
            'legal_disclaimer', 'related_law',
            'action_url', 'action_instructions',
            'is_ai_translated', 'ai_translations', 'ai_summary', 'ai_keywords',
            'approval_notes', 'approved_by',
            'gallery_images', 'translations', 'related_announcements',
            'acknowledgment_details', 'updated_at', 'last_promoted_at'
        ]

    def get_related_announcements(self, obj):
        # Get similar announcements
        related = Announcement.objects.filter(
            status='published',
            announcement_type=obj.announcement_type,
            is_active=True
        ).exclude(id=obj.id)[:5]

        return AnnouncementListSerializer(
            related,
            many=True,
            context=self.context
        ).data

    def get_acknowledgment_details(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.requires_acknowledgment:
            try:
                ack = AnnouncementAcknowledgment.objects.get(
                    announcement=obj,
                    user=request.user
                )
                return {
                    'acknowledged': True,
                    'acknowledged_at': ack.acknowledged_at
                }
            except AnnouncementAcknowledgment.DoesNotExist:
                return {
                    'acknowledged': False,
                    'acknowledged_at': None
                }
        return None


class AnnouncementCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating announcements"""
    tags_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    gallery_images = AnnouncementImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Announcement
        fields = [
            'title', 'summary', 'content',
            'announcement_type', 'category', 'tags_ids', 'target_audience',
            'source_organization', 'organization_logo', 'reference_number',
            'contact_person', 'contact_email', 'contact_phone',
            'contact_address', 'website_url', 'whatsapp_number',
            'is_national', 'regions', 'districts', 'location_details',
            'featured_image', 'document', 'document_title', 'video_url',
            'priority', 'is_emergency', 'is_pinned', 'is_featured',
            'publish_at', 'expires_at',
            'requires_acknowledgment', 'legal_disclaimer', 'related_law',
            'action_required', 'action_deadline', 'action_url', 'action_instructions',
            'status', 'gallery_images', 'uploaded_images'
        ]

    def create(self, validated_data):
        tags_ids = validated_data.pop('tags_ids', [])
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Create the announcement
        announcement = Announcement.objects.create(
            posted_by=self.context['request'].user,
            **validated_data
        )

        # Add tags
        if tags_ids:
            from tags.models import Tag, ContentTag
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='announcement',
                    object_id=announcement.id,
                    created_by=self.context['request'].user
                )
                tag.increment_usage()

        # Add gallery images
        for index, image in enumerate(uploaded_images):
            AnnouncementImage.objects.create(
                announcement=announcement,
                image=image,
                order=index
            )

        return announcement

    def update(self, instance, validated_data):
        tags_ids = validated_data.pop('tags_ids', None)
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Update announcement fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_ids is not None:
            from tags.models import Tag, ContentTag
            # Remove existing tags
            ContentTag.objects.filter(
                content_type='announcement',
                object_id=instance.id
            ).delete()

            # Add new tags
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='announcement',
                    object_id=instance.id,
                    created_by=self.context['request'].user
                )

        # Add new gallery images
        for index, image in enumerate(uploaded_images):
            AnnouncementImage.objects.create(
                announcement=instance,
                image=image,
                order=instance.gallery_images.count() + index
            )

        return instance


class AnnouncementAcknowledgmentSerializer(serializers.ModelSerializer):
    """Serializer for announcement acknowledgments"""
    user = UserMinimalSerializer(read_only=True)
    announcement_title = serializers.CharField(source='announcement.title', read_only=True)

    class Meta:
        model = AnnouncementAcknowledgment
        fields = [
            'id', 'announcement', 'announcement_title', 'user',
            'acknowledged_at', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'user', 'acknowledged_at', 'ip_address', 'user_agent']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user

        # Capture IP and user agent
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        validated_data['ip_address'] = ip
        validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        # Create acknowledgment
        acknowledgment = AnnouncementAcknowledgment.objects.create(**validated_data)

        # Update announcement count
        announcement = acknowledgment.announcement
        announcement.acknowledgments_count += 1
        announcement.save()

        return acknowledgment


class AnnouncementEngagementSerializer(serializers.Serializer):
    """Serializer for announcement engagement actions"""
    action = serializers.ChoiceField(choices=['view', 'share', 'acknowledge'])

    def save(self):
        announcement = self.context['view'].get_object()
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        action = self.validated_data['action']

        if action == 'view':
            announcement.increment_views()

            # Track view if user is authenticated
            if user:
                content_type = ContentType.objects.get_for_model(announcement)
                View.objects.get_or_create(
                    user=user,
                    content_type=content_type,
                    object_id=announcement.id
                )

        elif action == 'share':
            announcement.shares_count += 1
            announcement.save()

            # Track share if user is authenticated
            if user:
                content_type = ContentType.objects.get_for_model(announcement)
                Share.objects.create(
                    user=user,
                    content_type=content_type,
                    object_id=announcement.id,
                    platform='direct'
                )

        elif action == 'acknowledge' and user:
            # Handle acknowledgment via AnnouncementAcknowledgmentSerializer
            pass

        return announcement


class AnnouncementTranslationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating announcement translations"""

    class Meta:
        model = AnnouncementTranslation
        fields = [
            'announcement', 'language', 'title', 'summary', 'content',
            'is_machine_translated'
        ]

    def create(self, validated_data):
        # Check if user is authorized to verify translations
        if not validated_data.get('is_machine_translated', True):
            validated_data['verified_by'] = self.context['request'].user

        return AnnouncementTranslation.objects.create(**validated_data)


class AnnouncementAlertSerializer(serializers.ModelSerializer):
    """Serializer for announcement alerts"""
    sent_by = UserMinimalSerializer(read_only=True)
    announcement_title = serializers.CharField(source='announcement.title', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)

    class Meta:
        model = AnnouncementAlert
        fields = [
            'id', 'announcement', 'announcement_title',
            'alert_type', 'alert_type_display', 'recipient_count', 'message',
            'is_sent', 'sent_at', 'failed_count',
            'created_at', 'sent_by'
        ]
        read_only_fields = ['id', 'is_sent', 'sent_at', 'failed_count', 'created_at', 'sent_by']

    def create(self, validated_data):
        validated_data['sent_by'] = self.context['request'].user
        return AnnouncementAlert.objects.create(**validated_data)


class AnnouncementPromoteSerializer(serializers.Serializer):
    """Serializer for promoting announcements"""
    promote_as = serializers.ChoiceField(choices=['emergency', 'pinned', 'featured'])
    duration_hours = serializers.IntegerField(min_value=1, max_value=168, default=24)

    def save(self):
        announcement = self.context['view'].get_object()
        promote_as = self.validated_data['promote_as']
        duration_hours = self.validated_data['duration_hours']

        if promote_as == 'emergency':
            announcement.is_emergency = True
        elif promote_as == 'pinned':
            announcement.is_pinned = True
        elif promote_as == 'featured':
            announcement.is_featured = True

        announcement.last_promoted_at = timezone.now()
        announcement.save()

        # TODO: Set up task to auto-demote after duration

        return announcement