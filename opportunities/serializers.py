from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    Opportunity, OpportunityImage, Application,
    SavedOpportunity, OpportunityAlert
)
from authentication.serializers import UserMinimalSerializer
from tags.serializers import TagSerializer, CategorySerializer
from interactions.models import Like, Share, View, Bookmark

User = get_user_model()


class OpportunityImageSerializer(serializers.ModelSerializer):
    """Serializer for opportunity gallery images"""

    class Meta:
        model = OpportunityImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class OpportunityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for opportunity lists"""
    posted_by = UserMinimalSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Display fields
    opportunity_type_display = serializers.CharField(
        source='get_opportunity_type_display', read_only=True)
    employment_type_display = serializers.CharField(
        source='get_employment_type_display', read_only=True)
    experience_level_display = serializers.CharField(
        source='get_experience_level_display', read_only=True)
    salary_range = serializers.CharField(read_only=True)

    # Engagement and status
    user_applied = serializers.SerializerMethodField()
    user_saved = serializers.SerializerMethodField()
    user_liked = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image',
            'opportunity_type', 'opportunity_type_display',
            'category', 'tags', 'posted_by',
            'organization_name', 'organization_logo', 'organization_verified',
            'location', 'city', 'region', 'country', 'is_remote', 'is_diaspora',
            'employment_type', 'employment_type_display',
            'experience_level', 'experience_level_display',
            'salary_range', 'show_salary',
            'funding_amount', 'funding_currency', 'duration',
            'deadline', 'days_until_deadline',
            'is_featured', 'is_trending', 'is_urgent', 'is_active',
            'views_count', 'applications_count', 'likes_count', 'shares_count',
            'user_applied', 'user_saved', 'user_liked',
            'status', 'created_at', 'published_at'
        ]

    def get_user_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Application.objects.filter(
                applicant=request.user,
                opportunity=obj
            ).exists()
        return False

    def get_user_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedOpportunity.objects.filter(
                user=request.user,
                opportunity=obj
            ).exists()
        return False

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


class OpportunityDetailSerializer(OpportunityListSerializer):
    """Detailed serializer for opportunity view"""
    gallery_images = OpportunityImageSerializer(many=True, read_only=True)

    # Related content
    related_opportunities = serializers.SerializerMethodField()
    similar_by_organization = serializers.SerializerMethodField()

    # Application info for owner
    recent_applications = serializers.SerializerMethodField()

    class Meta(OpportunityListSerializer.Meta):
        fields = OpportunityListSerializer.Meta.fields + [
            'description', 'organization_website', 'organization_description',
            'relocation_assistance', 'benefits',
            'education_requirement', 'experience_requirement',
            'skills_required', 'languages_required', 'certifications_required',
            'eligibility_criteria', 'selection_process', 'number_of_slots',
            'application_method', 'application_url', 'application_email',
            'application_instructions', 'required_documents',
            'contact_person', 'contact_email', 'contact_phone',
            'is_ai_enhanced', 'ai_summary', 'ai_match_keywords',
            'gallery_images', 'related_opportunities', 'similar_by_organization',
            'recent_applications', 'updated_at'
        ]

    def get_related_opportunities(self, obj):
        # Get similar opportunities based on type and category
        related = Opportunity.objects.filter(
            status='published',
            opportunity_type=obj.opportunity_type,
            is_active=True
        ).exclude(id=obj.id)[:5]

        return OpportunityListSerializer(
            related,
            many=True,
            context=self.context
        ).data

    def get_similar_by_organization(self, obj):
        # Get other opportunities from same organization
        similar = Opportunity.objects.filter(
            status='published',
            organization_name=obj.organization_name,
            is_active=True
        ).exclude(id=obj.id)[:3]

        return OpportunityListSerializer(
            similar,
            many=True,
            context=self.context
        ).data

    def get_recent_applications(self, obj):
        # Only show to owner or admin
        request = self.context.get('request')
        if request and (request.user == obj.posted_by or request.user.is_staff):
            applications = Application.objects.filter(
                opportunity=obj,
                status='submitted'
            ).select_related('applicant')[:5]

            return ApplicationMinimalSerializer(
                applications,
                many=True,
                context=self.context
            ).data
        return []


class OpportunityCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating opportunities"""
    tags_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    gallery_images = OpportunityImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Opportunity
        fields = [
            'title', 'summary', 'description',
            'opportunity_type', 'category', 'tags_ids',
            'organization_name', 'organization_logo', 'organization_website',
            'organization_description', 'organization_verified',
            'location', 'city', 'region', 'country', 'is_remote', 'is_diaspora',
            'relocation_assistance', 'featured_image',
            'employment_type', 'experience_level',
            'salary_min', 'salary_max', 'salary_currency', 'show_salary', 'benefits',
            'education_requirement', 'experience_requirement',
            'skills_required', 'languages_required', 'certifications_required',
            'funding_amount', 'funding_currency', 'duration',
            'eligibility_criteria', 'selection_process', 'number_of_slots',
            'application_method', 'application_url', 'application_email',
            'application_instructions', 'required_documents', 'deadline',
            'contact_person', 'contact_email', 'contact_phone',
            'is_featured', 'is_trending', 'is_urgent', 'status',
            'gallery_images', 'uploaded_images'
        ]

    def create(self, validated_data):
        tags_ids = validated_data.pop('tags_ids', [])
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Create the opportunity
        opportunity = Opportunity.objects.create(
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
                    content_type='opportunity',
                    object_id=opportunity.id,
                    created_by=self.context['request'].user
                )
                tag.increment_usage()

        # Add gallery images
        for index, image in enumerate(uploaded_images):
            OpportunityImage.objects.create(
                opportunity=opportunity,
                image=image,
                order=index
            )

        return opportunity

    def update(self, instance, validated_data):
        tags_ids = validated_data.pop('tags_ids', None)
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Update opportunity fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_ids is not None:
            from tags.models import Tag, ContentTag
            # Remove existing tags
            ContentTag.objects.filter(
                content_type='opportunity',
                object_id=instance.id
            ).delete()

            # Add new tags
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='opportunity',
                    object_id=instance.id,
                    created_by=self.context['request'].user
                )

        # Add new gallery images
        for index, image in enumerate(uploaded_images):
            OpportunityImage.objects.create(
                opportunity=instance,
                image=image,
                order=instance.gallery_images.count() + index
            )

        return instance


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications"""
    applicant = UserMinimalSerializer(read_only=True)
    opportunity = serializers.PrimaryKeyRelatedField(
        queryset=Opportunity.objects.all(),
        write_only=True
    )
    opportunity_details = OpportunityListSerializer(
        source='opportunity', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'opportunity', 'opportunity_details', 'applicant',
            'full_name', 'email', 'phone', 'location',
            'cv_file', 'cover_letter', 'portfolio_url', 'linkedin_url',
            'years_of_experience', 'current_position', 'current_company',
            'expected_salary', 'availability', 'references',
            'status', 'status_display', 'reviewer_notes',
            'interview_date', 'interview_location',
            'ai_match_score', 'ai_match_reasons',
            'created_at', 'submitted_at', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'applicant', 'status', 'reviewer_notes',
            'interview_date', 'interview_location',
            'ai_match_score', 'ai_match_reasons',
            'created_at', 'submitted_at', 'reviewed_at'
        ]

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        application = Application.objects.create(**validated_data)

        # Auto-fill from user profile if available
        user = self.context['request'].user
        if not application.full_name:
            application.full_name = user.get_full_name()
        if not application.email:
            application.email = user.email
        application.save()

        return application


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications"""

    class Meta:
        model = Application
        fields = [
            'opportunity', 'full_name', 'email', 'phone', 'location',
            'cv_file', 'cover_letter', 'portfolio_url', 'linkedin_url',
            'years_of_experience', 'current_position', 'current_company',
            'expected_salary', 'availability', 'references'
        ]

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        validated_data['status'] = 'submitted'
        validated_data['submitted_at'] = timezone.now()
        return super().create(validated_data)


class ApplicationMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for application lists"""
    applicant = UserMinimalSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'applicant', 'full_name', 'email',
            'status', 'status_display', 'ai_match_score',
            'created_at', 'submitted_at'
        ]


class SavedOpportunitySerializer(serializers.ModelSerializer):
    """Serializer for saved opportunities"""
    opportunity = OpportunityListSerializer(read_only=True)
    opportunity_id = serializers.PrimaryKeyRelatedField(
        queryset=Opportunity.objects.all(),
        source='opportunity',
        write_only=True
    )

    class Meta:
        model = SavedOpportunity
        fields = [
            'id', 'opportunity', 'opportunity_id',
            'notes', 'reminder_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OpportunityAlertSerializer(serializers.ModelSerializer):
    """Serializer for opportunity alerts"""
    matches_count = serializers.SerializerMethodField()

    class Meta:
        model = OpportunityAlert
        fields = [
            'id', 'name', 'opportunity_types', 'keywords',
            'location', 'is_remote_only', 'min_salary',
            'is_active', 'frequency', 'last_sent',
            'matches_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sent', 'created_at', 'updated_at']

    def get_matches_count(self, obj):
        # Count matching opportunities
        queryset = Opportunity.objects.filter(
            status='published',
            is_active=True
        )

        if obj.opportunity_types:
            queryset = queryset.filter(
                opportunity_type__in=obj.opportunity_types)

        if obj.is_remote_only:
            queryset = queryset.filter(is_remote=True)

        if obj.min_salary:
            queryset = queryset.filter(salary_min__gte=obj.min_salary)

        return queryset.count()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OpportunityEngagementSerializer(serializers.Serializer):
    """Serializer for opportunity engagement actions"""
    action = serializers.ChoiceField(
        choices=['like', 'unlike', 'save', 'unsave'])

    def save(self):
        opportunity = self.context['view'].get_object()
        user = self.context['request'].user
        action = self.validated_data['action']

        if action == 'like':
            content_type = ContentType.objects.get_for_model(opportunity)
            Like.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=opportunity.id
            )
            opportunity.likes_count += 1
            opportunity.save()
        elif action == 'unlike':
            content_type = ContentType.objects.get_for_model(opportunity)
            Like.objects.filter(
                user=user,
                content_type=content_type,
                object_id=opportunity.id
            ).delete()
            opportunity.likes_count = max(0, opportunity.likes_count - 1)
            opportunity.save()
        elif action == 'save':
            SavedOpportunity.objects.get_or_create(
                user=user,
                opportunity=opportunity
            )
            opportunity.bookmarks_count += 1
            opportunity.save()
        elif action == 'unsave':
            SavedOpportunity.objects.filter(
                user=user,
                opportunity=opportunity
            ).delete()
            opportunity.bookmarks_count = max(
                0, opportunity.bookmarks_count - 1)
            opportunity.save()

        return opportunity


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating application status"""
    status = serializers.ChoiceField(
        choices=Application.APPLICATION_STATUS_CHOICES)
    reviewer_notes = serializers.CharField(required=False, allow_blank=True)
    interview_date = serializers.DateTimeField(required=False, allow_null=True)
    interview_location = serializers.CharField(
        required=False, allow_blank=True)

    class Meta:
        model = Application
        fields = ['status', 'reviewer_notes',
                  'interview_date', 'interview_location']

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.reviewer_notes = validated_data.get(
            'reviewer_notes', instance.reviewer_notes)
        instance.interview_date = validated_data.get(
            'interview_date', instance.interview_date)
        instance.interview_location = validated_data.get(
            'interview_location', instance.interview_location)
        instance.reviewed_at = timezone.now()
        instance.save()

        # Send notification to applicant about status change
        # TODO: Implement notification system

        return instance
