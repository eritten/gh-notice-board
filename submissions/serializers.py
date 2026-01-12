from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    ContentSubmission, ContactMessage, FeedbackSubmission, ReportSubmission
)
from authentication.serializers import UserMinimalSerializer

User = get_user_model()


class ContentSubmissionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for content submission lists"""
    submitted_by = UserMinimalSerializer(read_only=True)
    submission_type_display = serializers.CharField(source='get_submission_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    reviewed_by = UserMinimalSerializer(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    can_edit = serializers.BooleanField(read_only=True)

    class Meta:
        model = ContentSubmission
        fields = [
            'id', 'submission_type', 'submission_type_display',
            'title', 'slug', 'summary',
            'submitted_by', 'submitter_name', 'submitter_email', 'submitter_organization',
            'priority', 'priority_display',
            'status', 'status_display',
            'is_anonymous', 'is_exclusive', 'requires_fact_check',
            'is_pending', 'can_edit',
            'reviewed_by', 'created_at', 'submitted_at', 'reviewed_at'
        ]


class ContentSubmissionDetailSerializer(ContentSubmissionListSerializer):
    """Detailed serializer for content submission view"""

    class Meta(ContentSubmissionListSerializer.Meta):
        fields = ContentSubmissionListSerializer.Meta.fields + [
            'content', 'submitter_phone', 'submitter_location',
            'location', 'event_date', 'tags', 'sources', 'additional_info',
            'featured_image', 'document', 'document_title', 'additional_images',
            'reviewer_notes', 'rejection_reason', 'fact_check_notes',
            'published_as_type', 'published_as_id', 'published_url',
            'compensation_offered', 'compensation_amount', 'payment_status', 'payment_notes',
            'copyright_agreement', 'verification_consent',
            'views_count', 'updated_at', 'published_at'
        ]


class ContentSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating content submissions"""

    class Meta:
        model = ContentSubmission
        fields = [
            'submission_type', 'title', 'summary', 'content',
            'submitter_name', 'submitter_email', 'submitter_phone',
            'submitter_organization', 'submitter_location',
            'location', 'event_date', 'tags', 'sources', 'additional_info',
            'featured_image', 'document', 'document_title',
            'is_anonymous', 'is_exclusive', 'requires_fact_check',
            'copyright_agreement', 'verification_consent'
        ]

    def validate(self, data):
        # Ensure copyright agreement is accepted
        if not data.get('copyright_agreement'):
            raise serializers.ValidationError("You must agree to the copyright terms.")

        # Ensure verification consent for fact-check requiring content
        if data.get('requires_fact_check') and not data.get('verification_consent'):
            raise serializers.ValidationError("Verification consent is required for fact-check content.")

        return data

    def create(self, validated_data):
        request = self.context.get('request')

        # Set submitter if authenticated
        if request and request.user.is_authenticated:
            validated_data['submitted_by'] = request.user
            if not validated_data.get('submitter_name'):
                validated_data['submitter_name'] = request.user.get_full_name()
            if not validated_data.get('submitter_email'):
                validated_data['submitter_email'] = request.user.email

        # Capture IP and user agent
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            validated_data['ip_address'] = ip
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        return ContentSubmission.objects.create(**validated_data)


class ContentSubmissionReviewSerializer(serializers.Serializer):
    """Serializer for reviewing content submissions"""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_info'])
    notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    fact_check_notes = serializers.CharField(required=False, allow_blank=True)
    compensation_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )

    def validate(self, data):
        action = data.get('action')
        if action == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required when rejecting.")
        return data

    def save(self):
        submission = self.context['submission']
        user = self.context['request'].user
        action = self.validated_data['action']

        if action == 'approve':
            submission.approve(user)
            if self.validated_data.get('compensation_amount'):
                submission.compensation_offered = True
                submission.compensation_amount = self.validated_data['compensation_amount']
        elif action == 'reject':
            submission.reject(user, self.validated_data['rejection_reason'])
        elif action == 'request_info':
            submission.status = 'under_review'
            submission.reviewed_by = user

        if self.validated_data.get('notes'):
            submission.reviewer_notes = self.validated_data['notes']
        if self.validated_data.get('fact_check_notes'):
            submission.fact_check_notes = self.validated_data['fact_check_notes']

        submission.save()
        return submission


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for contact messages"""
    sender = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    inquiry_type_display = serializers.CharField(source='get_inquiry_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            'id', 'inquiry_type', 'inquiry_type_display',
            'subject', 'message',
            'sender', 'name', 'email', 'phone', 'organization', 'website', 'location',
            'referrer', 'attachment',
            'priority', 'priority_display',
            'is_read', 'is_responded', 'is_resolved', 'is_spam',
            'assigned_to', 'response_notes',
            'follow_up_required', 'follow_up_date',
            'created_at', 'read_at', 'responded_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'sender', 'is_read', 'is_responded', 'is_resolved',
            'assigned_to', 'created_at', 'read_at', 'responded_at', 'resolved_at'
        ]


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contact messages"""

    class Meta:
        model = ContactMessage
        fields = [
            'inquiry_type', 'subject', 'message',
            'name', 'email', 'phone', 'organization', 'website', 'location',
            'referrer', 'attachment'
        ]

    def create(self, validated_data):
        request = self.context.get('request')

        # Set sender if authenticated
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
            if not validated_data.get('name'):
                validated_data['name'] = request.user.get_full_name()
            if not validated_data.get('email'):
                validated_data['email'] = request.user.email

        # Capture IP and user agent
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            validated_data['ip_address'] = ip
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        # Auto-set priority based on inquiry type
        if validated_data.get('inquiry_type') in ['complaint', 'technical', 'press']:
            validated_data['priority'] = 'high'
        elif validated_data.get('inquiry_type') in ['partnership', 'advertising']:
            validated_data['priority'] = 'medium'

        return ContactMessage.objects.create(**validated_data)


class FeedbackSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for feedback submissions"""
    user = UserMinimalSerializer(read_only=True)
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = FeedbackSubmission
        fields = [
            'id', 'feedback_type', 'feedback_type_display',
            'title', 'description',
            'user', 'page_url', 'content_type', 'content_id',
            'overall_rating', 'ease_of_use_rating', 'content_quality_rating',
            'average_rating', 'would_recommend',
            'browser', 'device_type', 'screenshot',
            'is_reviewed', 'is_implemented', 'is_public',
            'admin_response', 'implementation_notes',
            'created_at', 'reviewed_at', 'implemented_at'
        ]
        read_only_fields = [
            'id', 'user', 'is_reviewed', 'is_implemented',
            'admin_response', 'implementation_notes',
            'created_at', 'reviewed_at', 'implemented_at'
        ]


class FeedbackSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating feedback submissions"""

    class Meta:
        model = FeedbackSubmission
        fields = [
            'feedback_type', 'title', 'description',
            'page_url', 'content_type', 'content_id',
            'overall_rating', 'ease_of_use_rating', 'content_quality_rating',
            'would_recommend', 'browser', 'device_type', 'screenshot'
        ]

    def create(self, validated_data):
        request = self.context.get('request')

        # Set user if authenticated
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        # Try to detect browser and device from user agent
        if request and not validated_data.get('browser'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            # Simple browser detection
            if 'Chrome' in user_agent:
                validated_data['browser'] = 'Chrome'
            elif 'Firefox' in user_agent:
                validated_data['browser'] = 'Firefox'
            elif 'Safari' in user_agent:
                validated_data['browser'] = 'Safari'
            elif 'Edge' in user_agent:
                validated_data['browser'] = 'Edge'

            # Simple device detection
            if 'Mobile' in user_agent:
                validated_data['device_type'] = 'Mobile'
            elif 'Tablet' in user_agent:
                validated_data['device_type'] = 'Tablet'
            else:
                validated_data['device_type'] = 'Desktop'

        return FeedbackSubmission.objects.create(**validated_data)


class ReportSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for report submissions"""
    reporter = UserMinimalSerializer(read_only=True)
    reported_user = UserMinimalSerializer(read_only=True)
    reviewed_by = UserMinimalSerializer(read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ReportSubmission
        fields = [
            'id', 'report_type', 'report_type_display',
            'description',
            'reported_content_type', 'reported_content_id',
            'reported_content_url', 'reported_user',
            'reporter',
            'screenshot', 'additional_info',
            'status', 'status_display',
            'reviewed_by', 'reviewer_notes', 'action_taken',
            'created_at', 'reviewed_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'reporter', 'status', 'reviewed_by',
            'reviewer_notes', 'action_taken',
            'created_at', 'reviewed_at', 'resolved_at'
        ]


class ReportSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating report submissions"""

    class Meta:
        model = ReportSubmission
        fields = [
            'report_type', 'description',
            'reported_content_type', 'reported_content_id',
            'reported_content_url', 'reported_user',
            'screenshot', 'additional_info'
        ]

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return ReportSubmission.objects.create(**validated_data)


class ReportReviewSerializer(serializers.Serializer):
    """Serializer for reviewing report submissions"""
    status = serializers.ChoiceField(choices=['reviewing', 'valid', 'invalid', 'resolved'])
    notes = serializers.CharField(required=False, allow_blank=True)
    action_taken = serializers.CharField(required=False, allow_blank=True)

    def save(self):
        report = self.context['report']
        user = self.context['request'].user

        report.status = self.validated_data['status']
        report.reviewed_by = user
        report.reviewed_at = timezone.now()

        if self.validated_data.get('notes'):
            report.reviewer_notes = self.validated_data['notes']
        if self.validated_data.get('action_taken'):
            report.action_taken = self.validated_data['action_taken']

        if report.status == 'resolved':
            report.resolved_at = timezone.now()

        report.save()
        return report