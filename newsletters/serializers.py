from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from .models import (
    NewsletterSubscriber, Newsletter, NewsletterEmail, NewsletterTemplate
)
from authentication.serializers import UserMinimalSerializer

User = get_user_model()


class NewsletterSubscriberListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for newsletter subscriber lists"""
    user = UserMinimalSerializer(read_only=True)
    frequency_display = serializers.CharField(
        source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    engagement_rate = serializers.FloatField(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    subscriptions = serializers.SerializerMethodField()

    class Meta:
        model = NewsletterSubscriber
        fields = [
            'id', 'email', 'user', 'first_name', 'last_name', 'full_name',
            'location', 'frequency', 'frequency_display',
            'status', 'status_display', 'is_active',
            'emails_sent', 'emails_opened', 'engagement_rate',
            'subscriptions', 'created_at'
        ]

    def get_subscriptions(self, obj):
        """Get active subscriptions"""
        subs = []
        if obj.subscribe_news:
            subs.append('news')
        if obj.subscribe_events:
            subs.append('events')
        if obj.subscribe_opportunities:
            subs.append('opportunities')
        if obj.subscribe_announcements:
            subs.append('announcements')
        if obj.subscribe_diaspora:
            subs.append('diaspora')
        if obj.subscribe_special:
            subs.append('special')
        return subs


class NewsletterSubscriberDetailSerializer(NewsletterSubscriberListSerializer):
    """Detailed serializer for newsletter subscriber view"""

    class Meta(NewsletterSubscriberListSerializer.Meta):
        fields = NewsletterSubscriberListSerializer.Meta.fields + [
            'phone', 'subscribe_news', 'subscribe_events', 'subscribe_opportunities',
            'subscribe_announcements', 'subscribe_diaspora', 'subscribe_special',
            'preferred_language', 'preferred_categories',
            'confirmed_at', 'referrer',
            'links_clicked', 'last_email_sent', 'last_opened',
            'unsubscribed_at', 'unsubscribe_reason',
            'updated_at'
        ]
        read_only_fields = ['confirmation_token', 'unsubscribe_token']


class NewsletterSubscriberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating newsletter subscriptions"""

    class Meta:
        model = NewsletterSubscriber
        fields = [
            'email', 'first_name', 'last_name', 'location', 'phone',
            'subscribe_news', 'subscribe_events', 'subscribe_opportunities',
            'subscribe_announcements', 'subscribe_diaspora', 'subscribe_special',
            'frequency', 'preferred_language', 'preferred_categories', 'referrer'
        ]

    def validate_email(self, value):
        if NewsletterSubscriber.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already subscribed.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            validated_data['ip_address'] = ip

        subscriber = NewsletterSubscriber.objects.create(**validated_data)
        subscriber.generate_tokens()
        return subscriber


class NewsletterSubscriberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating subscription preferences"""

    class Meta:
        model = NewsletterSubscriber
        fields = [
            'first_name', 'last_name', 'location', 'phone',
            'subscribe_news', 'subscribe_events', 'subscribe_opportunities',
            'subscribe_announcements', 'subscribe_diaspora', 'subscribe_special',
            'frequency', 'preferred_language', 'preferred_categories'
        ]


class NewsletterTemplateSerializer(serializers.ModelSerializer):
    """Serializer for newsletter templates"""
    created_by = UserMinimalSerializer(read_only=True)
    template_type_display = serializers.CharField(
        source='get_template_type_display', read_only=True)

    class Meta:
        model = NewsletterTemplate
        fields = [
            'id', 'name', 'slug', 'template_type', 'template_type_display',
            'description', 'html_template', 'text_template', 'css_styles',
            'has_header', 'has_footer', 'has_social_links', 'sections',
            'is_active', 'is_default', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug',
                            'created_by', 'created_at', 'updated_at']


class NewsletterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for newsletter lists"""
    created_by = UserMinimalSerializer(read_only=True)
    newsletter_type_display = serializers.CharField(
        source='get_newsletter_type_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    delivery_rate = serializers.FloatField(read_only=True)
    recipient_count = serializers.SerializerMethodField()

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'slug', 'newsletter_type', 'newsletter_type_display',
            'subject', 'preheader',
            'status', 'status_display',
            'recipient_count', 'recipients_count', 'sent_count', 'delivered_count',
            'open_rate', 'click_rate', 'delivery_rate',
            'is_ab_test', 'scheduled_for', 'sent_at',
            'created_by', 'created_at'
        ]

    def get_recipient_count(self, obj):
        if obj.status == 'draft':
            return obj.get_recipient_count()
        return obj.recipients_count


class NewsletterDetailSerializer(NewsletterListSerializer):
    """Detailed serializer for newsletter view"""
    approved_by = UserMinimalSerializer(read_only=True)
    featured_content = serializers.SerializerMethodField()

    class Meta(NewsletterListSerializer.Meta):
        fields = NewsletterListSerializer.Meta.fields + [
            'content_html', 'content_text', 'template_used',
            'featured_news', 'featured_events', 'featured_opportunities',
            'featured_announcements', 'featured_content',
            'send_to_all', 'target_segments',
            'send_to_news', 'send_to_events', 'send_to_opportunities',
            'send_to_announcements', 'send_to_diaspora', 'test_emails',
            'use_personalization', 'from_name', 'from_email', 'reply_to_email',
            'opened_count', 'clicked_count', 'unsubscribed_count',
            'bounced_count', 'complained_count',
            'ab_test_percentage', 'variant_subject', 'variant_content_html',
            'approved_by', 'approved_at', 'completed_at', 'updated_at'
        ]

    def get_featured_content(self, obj):
        """Get details of featured content"""
        return {
            'news': obj.featured_news or [],
            'events': obj.featured_events or [],
            'opportunities': obj.featured_opportunities or [],
            'announcements': obj.featured_announcements or []
        }


class NewsletterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating newsletters"""

    class Meta:
        model = Newsletter
        fields = [
            'title', 'newsletter_type', 'subject', 'preheader',
            'content_html', 'content_text', 'template_used',
            'featured_news', 'featured_events', 'featured_opportunities',
            'featured_announcements',
            'send_to_all', 'target_segments',
            'send_to_news', 'send_to_events', 'send_to_opportunities',
            'send_to_announcements', 'send_to_diaspora', 'test_emails',
            'use_personalization', 'from_name', 'from_email', 'reply_to_email',
            'is_ab_test', 'ab_test_percentage', 'variant_subject', 'variant_content_html'
        ]

    def validate(self, data):
        if not data.get('send_to_all'):
            has_target = any([
                data.get('send_to_news'),
                data.get('send_to_events'),
                data.get('send_to_opportunities'),
                data.get('send_to_announcements'),
                data.get('send_to_diaspora'),
                data.get('target_segments')
            ])
            if not has_target:
                raise serializers.ValidationError(
                    "You must select at least one target audience.")

        if data.get('is_ab_test'):
            if not data.get('variant_subject') and not data.get('variant_content_html'):
                raise serializers.ValidationError(
                    "A/B tests require at least one variant.")

        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return Newsletter.objects.create(**validated_data)


class NewsletterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating newsletters"""

    class Meta:
        model = Newsletter
        fields = [
            'title', 'subject', 'preheader',
            'content_html', 'content_text', 'template_used',
            'featured_news', 'featured_events', 'featured_opportunities',
            'featured_announcements',
            'send_to_all', 'target_segments',
            'send_to_news', 'send_to_events', 'send_to_opportunities',
            'send_to_announcements', 'send_to_diaspora', 'test_emails',
            'use_personalization', 'from_name', 'from_email', 'reply_to_email',
            'is_ab_test', 'ab_test_percentage', 'variant_subject', 'variant_content_html'
        ]

    def validate(self, data):
        if self.instance.status in ['sending', 'sent']:
            raise serializers.ValidationError(
                "Cannot update a newsletter that has been sent.")
        return data


class NewsletterScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling newsletters"""
    scheduled_for = serializers.DateTimeField()

    def validate_scheduled_for(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Scheduled time must be in the future.")
        return value

    def save(self):
        newsletter = self.context['newsletter']
        newsletter.schedule(self.validated_data['scheduled_for'])
        return newsletter


class NewsletterTestSerializer(serializers.Serializer):
    """Serializer for sending test emails"""
    test_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=10
    )

    def save(self):
        newsletter = self.context['newsletter']
        newsletter.send_test_email(self.validated_data['test_emails'])
        return newsletter


class NewsletterEmailSerializer(serializers.ModelSerializer):
    """Serializer for individual newsletter emails"""
    newsletter = serializers.CharField(
        source='newsletter.title', read_only=True)
    subscriber_email = serializers.CharField(
        source='subscriber.email', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = NewsletterEmail
        fields = [
            'id', 'newsletter', 'subscriber_email',
            'status', 'status_display', 'email_id',
            'sent_at', 'delivered_at', 'opened_at', 'first_click_at',
            'open_count', 'click_count', 'clicked_links',
            'is_variant', 'bounce_type', 'bounce_reason'
        ]


class NewsletterAnalyticsSerializer(serializers.Serializer):
    """Serializer for newsletter analytics"""
    newsletter_id = serializers.UUIDField()
    title = serializers.CharField()
    subject = serializers.CharField()
    sent_at = serializers.DateTimeField()

    recipients_count = serializers.IntegerField()
    sent_count = serializers.IntegerField()
    delivered_count = serializers.IntegerField()
    delivery_rate = serializers.FloatField()

    opened_count = serializers.IntegerField()
    open_rate = serializers.FloatField()
    unique_opens = serializers.IntegerField()
    clicked_count = serializers.IntegerField()
    click_rate = serializers.FloatField()
    unique_clicks = serializers.IntegerField()

    unsubscribed_count = serializers.IntegerField()
    unsubscribe_rate = serializers.FloatField()
    bounced_count = serializers.IntegerField()
    bounce_rate = serializers.FloatField()
    complained_count = serializers.IntegerField()
    complaint_rate = serializers.FloatField()

    link_clicks = serializers.ListField(
        child=serializers.DictField(), required=False)
    device_stats = serializers.DictField(required=False)
    client_stats = serializers.DictField(required=False)
    hourly_opens = serializers.ListField(
        child=serializers.DictField(), required=False)
    ab_test_results = serializers.DictField(required=False)


class BulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on subscribers"""
    subscriber_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ])

    def save(self):
        subscribers = NewsletterSubscriber.objects.filter(
            id__in=self.validated_data['subscriber_ids']
        )
        action = self.validated_data['action']

        if action == 'activate':
            subscribers.update(status='active', confirmed_at=timezone.now())
        elif action == 'deactivate':
            subscribers.update(status='unsubscribed')
        elif action == 'delete':
            subscribers.delete()
        elif action == 'export':
            return NewsletterSubscriberDetailSerializer(subscribers, many=True).data

        return {'affected': subscribers.count()}


class UnsubscribeSerializer(serializers.Serializer):
    """Serializer for unsubscribing"""
    token = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate_token(self, value):
        try:
            subscriber = NewsletterSubscriber.objects.get(
                unsubscribe_token=value)
            self.context['subscriber'] = subscriber
        except NewsletterSubscriber.DoesNotExist:
            raise serializers.ValidationError("Invalid unsubscribe token.")
        return value

    def save(self):
        subscriber = self.context['subscriber']
        reason = self.validated_data.get('reason', '')
        subscriber.unsubscribe(reason)
        return subscriber
