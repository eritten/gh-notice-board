from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    DiasporaPost, DiasporaImage, DiasporaNetwork,
    DiasporaDirectory, DiasporaInvestment
)
from authentication.serializers import UserMinimalSerializer
from tags.serializers import TagSerializer, CategorySerializer
from interactions.models import Like, Comment, Share, View, Bookmark

User = get_user_model()


class DiasporaImageSerializer(serializers.ModelSerializer):
    """Serializer for diaspora post gallery images"""

    class Meta:
        model = DiasporaImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class DiasporaPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for diaspora post lists"""
    author = UserMinimalSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Display fields
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)

    # Engagement and status
    user_liked = serializers.SerializerMethodField()
    user_bookmarked = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_event = serializers.BooleanField(read_only=True)
    is_upcoming_event = serializers.BooleanField(read_only=True)
    is_investment_opportunity = serializers.BooleanField(read_only=True)

    class Meta:
        model = DiasporaPost
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image',
            'content_type', 'content_type_display',
            'category', 'tags', 'author', 'is_diaspora_author',
            'region', 'region_display', 'country', 'city', 'diaspora_community',
            'organization_name', 'organization_logo', 'organization_verified',
            'is_featured', 'is_trending', 'is_urgent', 'is_pinned',
            'views_count', 'likes_count', 'comments_count', 'shares_count',
            'user_liked', 'user_bookmarked',
            'is_active', 'is_event', 'is_upcoming_event', 'is_investment_opportunity',
            'event_date', 'opportunity_deadline',
            'investment_amount', 'investment_currency',
            'status', 'created_at', 'published_at'
        ]

    def get_user_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False

    def get_user_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Bookmark.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False


class DiasporaPostDetailSerializer(DiasporaPostListSerializer):
    """Detailed serializer for diaspora post view"""
    gallery_images = DiasporaImageSerializer(many=True, read_only=True)

    # Related content
    related_posts = serializers.SerializerMethodField()
    from_same_organization = serializers.SerializerMethodField()

    class Meta(DiasporaPostListSerializer.Meta):
        fields = DiasporaPostListSerializer.Meta.fields + [
            'content', 'organization_type',
            'contact_person', 'contact_email', 'contact_phone',
            'whatsapp_number', 'website_url', 'social_media_links',
            'featured_video_url',
            'allow_comments', 'allow_sharing', 'requires_membership',
            'partnership_type', 'event_location', 'event_registration_url',
            'is_ai_translated', 'ai_translations', 'ai_summary', 'ai_tags',
            'gallery_images', 'related_posts', 'from_same_organization',
            'updated_at'
        ]

    def get_related_posts(self, obj):
        # Get similar posts based on type and region
        related = DiasporaPost.objects.filter(
            status='published',
            content_type=obj.content_type,
            is_active=True
        ).exclude(id=obj.id)[:5]

        return DiasporaPostListSerializer(
            related,
            many=True,
            context=self.context
        ).data

    def get_from_same_organization(self, obj):
        if obj.organization_name:
            similar = DiasporaPost.objects.filter(
                status='published',
                organization_name=obj.organization_name,
                is_active=True
            ).exclude(id=obj.id)[:3]

            return DiasporaPostListSerializer(
                similar,
                many=True,
                context=self.context
            ).data
        return []


class DiasporaPostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating diaspora posts"""
    tags_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    gallery_images = DiasporaImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = DiasporaPost
        fields = [
            'title', 'summary', 'content',
            'content_type', 'category', 'tags_ids',
            'is_diaspora_author',
            'region', 'country', 'city', 'diaspora_community',
            'organization_name', 'organization_type', 'organization_logo',
            'featured_image', 'featured_video_url',
            'contact_person', 'contact_email', 'contact_phone',
            'whatsapp_number', 'website_url', 'social_media_links',
            'allow_comments', 'allow_sharing', 'requires_membership',
            'investment_amount', 'investment_currency', 'partnership_type',
            'opportunity_deadline',
            'event_date', 'event_location', 'event_registration_url',
            'is_featured', 'is_trending', 'is_urgent', 'is_pinned',
            'status', 'gallery_images', 'uploaded_images'
        ]

    def create(self, validated_data):
        tags_ids = validated_data.pop('tags_ids', [])
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Create the post
        post = DiasporaPost.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        # Add tags
        if tags_ids:
            from tags.models import Tag, ContentTag
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='diaspora',
                    object_id=post.id,
                    created_by=self.context['request'].user
                )
                tag.increment_usage()

        # Add gallery images
        for index, image in enumerate(uploaded_images):
            DiasporaImage.objects.create(
                post=post,
                image=image,
                order=index
            )

        return post

    def update(self, instance, validated_data):
        tags_ids = validated_data.pop('tags_ids', None)
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Update post fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_ids is not None:
            from tags.models import Tag, ContentTag
            # Remove existing tags
            ContentTag.objects.filter(
                content_type='diaspora',
                object_id=instance.id
            ).delete()

            # Add new tags
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='diaspora',
                    object_id=instance.id,
                    created_by=self.context['request'].user
                )

        # Add new gallery images
        for index, image in enumerate(uploaded_images):
            DiasporaImage.objects.create(
                post=instance,
                image=image,
                order=instance.gallery_images.count() + index
            )

        return instance


class DiasporaNetworkSerializer(serializers.ModelSerializer):
    """Serializer for diaspora networks"""
    created_by = UserMinimalSerializer(read_only=True)
    verified_by = UserMinimalSerializer(read_only=True)
    network_type_display = serializers.CharField(source='get_network_type_display', read_only=True)

    class Meta:
        model = DiasporaNetwork
        fields = [
            'id', 'name', 'slug', 'description', 'mission',
            'network_type', 'network_type_display',
            'founded_year', 'registration_number',
            'based_in_country', 'based_in_city', 'chapters',
            'president_name', 'contact_person', 'contact_email',
            'contact_phone', 'office_address',
            'website_url', 'facebook_url', 'twitter_handle',
            'linkedin_url', 'whatsapp_group',
            'membership_count', 'membership_fee', 'membership_currency',
            'membership_requirements',
            'logo', 'cover_image',
            'is_verified', 'verified_by', 'verified_at',
            'is_active', 'last_activity', 'events_count', 'projects_count',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = [
            'id', 'slug', 'is_verified', 'verified_by', 'verified_at',
            'created_at', 'updated_at', 'created_by'
        ]


class DiasporaNetworkCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating diaspora networks"""

    class Meta:
        model = DiasporaNetwork
        fields = [
            'name', 'description', 'mission',
            'network_type', 'founded_year', 'registration_number',
            'based_in_country', 'based_in_city', 'chapters',
            'president_name', 'contact_person', 'contact_email',
            'contact_phone', 'office_address',
            'website_url', 'facebook_url', 'twitter_handle',
            'linkedin_url', 'whatsapp_group',
            'membership_fee', 'membership_currency', 'membership_requirements',
            'logo', 'cover_image'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return DiasporaNetwork.objects.create(**validated_data)


class DiasporaDirectorySerializer(serializers.ModelSerializer):
    """Serializer for diaspora directory listings"""
    user = UserMinimalSerializer(read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    profession_display = serializers.CharField(source='get_profession_display', read_only=True)

    class Meta:
        model = DiasporaDirectory
        fields = [
            'id', 'user', 'listing_type', 'listing_type_display',
            'full_name', 'professional_title', 'profession', 'profession_display',
            'specialization', 'years_experience',
            'business_name', 'business_type', 'services_offered',
            'current_country', 'current_city', 'origin_region',
            'email', 'phone', 'whatsapp', 'website', 'linkedin',
            'qualifications', 'certifications', 'languages', 'availability',
            'profile_photo', 'business_logo',
            'is_verified', 'is_active', 'is_featured', 'allow_contact',
            'profile_views', 'contact_requests',
            'created_at', 'updated_at', 'last_active'
        ]
        read_only_fields = [
            'id', 'user', 'is_verified', 'profile_views', 'contact_requests',
            'created_at', 'updated_at', 'last_active'
        ]


class DiasporaDirectoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating directory listings"""

    class Meta:
        model = DiasporaDirectory
        fields = [
            'listing_type', 'full_name', 'professional_title',
            'profession', 'specialization', 'years_experience',
            'business_name', 'business_type', 'services_offered',
            'current_country', 'current_city', 'origin_region',
            'email', 'phone', 'whatsapp', 'website', 'linkedin',
            'qualifications', 'certifications', 'languages', 'availability',
            'profile_photo', 'business_logo', 'verification_documents',
            'allow_contact'
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Auto-fill full_name if not provided
        if not validated_data.get('full_name'):
            validated_data['full_name'] = validated_data['user'].get_full_name()
        return DiasporaDirectory.objects.create(**validated_data)


class DiasporaInvestmentSerializer(serializers.ModelSerializer):
    """Serializer for diaspora investment opportunities"""
    posted_by = UserMinimalSerializer(read_only=True)
    investment_type_display = serializers.CharField(source='get_investment_type_display', read_only=True)
    investment_stage_display = serializers.CharField(source='get_investment_stage_display', read_only=True)
    is_deadline_passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = DiasporaInvestment
        fields = [
            'id', 'title', 'slug', 'summary', 'description',
            'investment_type', 'investment_type_display',
            'investment_stage', 'investment_stage_display',
            'sector',
            'minimum_investment', 'maximum_investment', 'currency',
            'expected_return', 'payback_period',
            'location_country', 'location_region', 'location_city',
            'company_name', 'company_registration',
            'established_year', 'team_size',
            'contact_person', 'contact_title', 'contact_email', 'contact_phone',
            'business_plan', 'financial_projections', 'pitch_deck',
            'featured_image',
            'is_verified', 'risk_assessment',
            'is_active', 'is_featured', 'deadline', 'is_deadline_passed',
            'views_count', 'inquiries_count',
            'posted_by', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'slug', 'is_verified', 'views_count', 'inquiries_count',
            'posted_by', 'created_at', 'updated_at', 'published_at'
        ]


class DiasporaInvestmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating investment opportunities"""

    class Meta:
        model = DiasporaInvestment
        fields = [
            'title', 'summary', 'description',
            'investment_type', 'investment_stage', 'sector',
            'minimum_investment', 'maximum_investment', 'currency',
            'expected_return', 'payback_period',
            'location_country', 'location_region', 'location_city',
            'company_name', 'company_registration',
            'established_year', 'team_size',
            'contact_person', 'contact_title', 'contact_email', 'contact_phone',
            'business_plan', 'financial_projections', 'pitch_deck',
            'featured_image', 'deadline'
        ]

    def create(self, validated_data):
        validated_data['posted_by'] = self.context['request'].user
        return DiasporaInvestment.objects.create(**validated_data)


class DiasporaEngagementSerializer(serializers.Serializer):
    """Serializer for diaspora engagement actions"""
    action = serializers.ChoiceField(choices=['like', 'unlike', 'bookmark', 'unbookmark'])

    def save(self):
        post = self.context['view'].get_object()
        user = self.context['request'].user
        action = self.validated_data['action']
        content_type = ContentType.objects.get_for_model(post)

        if action == 'like':
            Like.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=post.id
            )
            post.likes_count += 1
        elif action == 'unlike':
            Like.objects.filter(
                user=user,
                content_type=content_type,
                object_id=post.id
            ).delete()
            post.likes_count = max(0, post.likes_count - 1)
        elif action == 'bookmark':
            Bookmark.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=post.id
            )
            post.bookmarks_count += 1
        elif action == 'unbookmark':
            Bookmark.objects.filter(
                user=user,
                content_type=content_type,
                object_id=post.id
            ).delete()
            post.bookmarks_count = max(0, post.bookmarks_count - 1)

        post.save()
        return post


class DiasporaDirectoryContactSerializer(serializers.Serializer):
    """Serializer for contacting directory listings"""
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    sender_name = serializers.CharField(max_length=200)
    sender_email = serializers.EmailField()
    sender_phone = serializers.CharField(max_length=20, required=False)

    def save(self):
        listing = self.context['view'].get_object()

        # Increment contact requests
        listing.contact_requests += 1
        listing.save()

        # TODO: Send email notification to listing owner

        return listing