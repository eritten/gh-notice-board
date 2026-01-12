import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class NewsletterSubscriber(models.Model):
    """Enhanced newsletter subscribers with preferences and tracking"""

    SUBSCRIPTION_FREQUENCY_CHOICES = [
        ('instant', 'Instant'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('monthly', 'Monthly Roundup'),
    ]

    SUBSCRIPTION_STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletter_subscription'
    )

    # Subscriber info
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Subscription preferences
    subscribe_news = models.BooleanField(default=True, help_text="News updates")
    subscribe_events = models.BooleanField(default=True, help_text="Event announcements")
    subscribe_opportunities = models.BooleanField(default=True, help_text="Job and opportunity alerts")
    subscribe_announcements = models.BooleanField(default=True, help_text="Official announcements")
    subscribe_diaspora = models.BooleanField(default=False, help_text="Diaspora updates")
    subscribe_special = models.BooleanField(default=True, help_text="Special offers and promotions")

    # Frequency and language
    frequency = models.CharField(max_length=10, choices=SUBSCRIPTION_FREQUENCY_CHOICES, default='weekly')
    preferred_language = models.CharField(max_length=10, default='en', help_text="Preferred language code")
    preferred_categories = models.JSONField(default=list, blank=True, help_text="List of category IDs")

    # Status and verification
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='pending')
    confirmation_token = models.CharField(max_length=100, blank=True, unique=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    referrer = models.CharField(max_length=200, blank=True, help_text="How they subscribed")

    # Engagement tracking
    emails_sent = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    links_clicked = models.PositiveIntegerField(default=0)
    last_email_sent = models.DateTimeField(blank=True, null=True)
    last_opened = models.DateTimeField(blank=True, null=True)

    # Unsubscribe info
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    unsubscribe_reason = models.TextField(blank=True)
    unsubscribe_token = models.CharField(max_length=100, blank=True, unique=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Newsletter Subscribers"
        indexes = [
            models.Index(fields=['status', 'frequency']),
            models.Index(fields=['email']),
            models.Index(fields=['confirmation_token']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_status_display()})"

    def generate_tokens(self):
        import secrets
        self.confirmation_token = secrets.token_urlsafe(32)
        self.unsubscribe_token = secrets.token_urlsafe(32)
        self.save()

    def confirm_subscription(self):
        self.status = 'active'
        self.confirmed_at = timezone.now()
        self.save()

    def unsubscribe(self, reason=''):
        self.status = 'unsubscribed'
        self.unsubscribed_at = timezone.now()
        if reason:
            self.unsubscribe_reason = reason
        self.save()

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def engagement_rate(self):
        if self.emails_sent == 0:
            return 0
        return (self.emails_opened / self.emails_sent) * 100

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.email.split('@')[0]


class Newsletter(models.Model):
    """Enhanced newsletter campaigns with templates and analytics"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]

    NEWSLETTER_TYPE_CHOICES = [
        ('regular', 'Regular Newsletter'),
        ('special', 'Special Announcement'),
        ('digest', 'Weekly/Monthly Digest'),
        ('breaking', 'Breaking News'),
        ('promotional', 'Promotional'),
        ('event', 'Event Invitation'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300, help_text="Internal title")
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    newsletter_type = models.CharField(max_length=20, choices=NEWSLETTER_TYPE_CHOICES, default='regular')

    # Email content
    subject = models.CharField(max_length=200, help_text="Email subject line")
    preheader = models.CharField(max_length=200, blank=True, help_text="Preview text")
    content_html = models.TextField(help_text="HTML content")
    content_text = models.TextField(help_text="Plain text content")
    template_used = models.CharField(max_length=100, blank=True)

    # Featured content
    featured_news = models.JSONField(default=list, blank=True, help_text="List of news IDs")
    featured_events = models.JSONField(default=list, blank=True, help_text="List of event IDs")
    featured_opportunities = models.JSONField(default=list, blank=True, help_text="List of opportunity IDs")
    featured_announcements = models.JSONField(default=list, blank=True, help_text="List of announcement IDs")

    # Targeting
    send_to_all = models.BooleanField(default=False)
    target_segments = models.JSONField(default=dict, blank=True, help_text="Segment targeting criteria")
    send_to_news = models.BooleanField(default=False)
    send_to_events = models.BooleanField(default=False)
    send_to_opportunities = models.BooleanField(default=False)
    send_to_announcements = models.BooleanField(default=False)
    send_to_diaspora = models.BooleanField(default=False)
    test_emails = models.JSONField(default=list, blank=True, help_text="List of test email addresses")

    # Personalization
    use_personalization = models.BooleanField(default=True)
    from_name = models.CharField(max_length=100, default="Ghana Notice Board")
    from_email = models.EmailField(default="newsletter@ghanaticeboard.com")
    reply_to_email = models.EmailField(blank=True)

    # Status and scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_for = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Metrics
    recipients_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    unsubscribed_count = models.PositiveIntegerField(default=0)
    bounced_count = models.PositiveIntegerField(default=0)
    complained_count = models.PositiveIntegerField(default=0)

    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_test_percentage = models.PositiveIntegerField(default=50)
    variant_subject = models.CharField(max_length=200, blank=True)
    variant_content_html = models.TextField(blank=True)

    # Created by
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_newsletters'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_newsletters'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Newsletter.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    @property
    def open_rate(self):
        if self.sent_count == 0:
            return 0
        return (self.opened_count / self.sent_count) * 100

    @property
    def click_rate(self):
        if self.sent_count == 0:
            return 0
        return (self.clicked_count / self.sent_count) * 100

    @property
    def delivery_rate(self):
        if self.sent_count == 0:
            return 0
        return (self.delivered_count / self.sent_count) * 100

    def get_recipient_count(self):
        """Calculate number of recipients based on targeting"""
        from .utils import calculate_recipients
        return calculate_recipients(self)

    def send_test_email(self, test_emails):
        """Send test emails"""
        # TODO: Implement test email sending
        pass

    def schedule(self, scheduled_time):
        """Schedule newsletter for sending"""
        self.scheduled_for = scheduled_time
        self.status = 'scheduled'
        self.save()

    def cancel(self):
        """Cancel scheduled newsletter"""
        if self.status == 'scheduled':
            self.status = 'cancelled'
            self.save()


class NewsletterEmail(models.Model):
    """Track individual email sends"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('unsubscribed', 'Unsubscribed'),
    ]

    # Relations
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE, related_name='emails')
    subscriber = models.ForeignKey(NewsletterSubscriber, on_delete=models.CASCADE, related_name='emails')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email_id = models.CharField(max_length=200, blank=True, help_text="Email service provider ID")

    # Tracking
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    first_click_at = models.DateTimeField(blank=True, null=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    # Engagement
    open_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    clicked_links = models.JSONField(default=list, blank=True)

    # Error tracking
    bounce_type = models.CharField(max_length=50, blank=True)
    bounce_reason = models.TextField(blank=True)

    # A/B Testing
    is_variant = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']
        unique_together = ['newsletter', 'subscriber']
        indexes = [
            models.Index(fields=['newsletter', 'status']),
            models.Index(fields=['subscriber']),
        ]

    def __str__(self):
        return f"{self.newsletter.title} to {self.subscriber.email}"

    def mark_opened(self):
        if self.status not in ['opened', 'clicked']:
            self.status = 'opened'
            self.opened_at = timezone.now()
            self.open_count += 1
            self.save()

            # Update newsletter stats
            if self.open_count == 1:
                self.newsletter.opened_count += 1
                self.newsletter.save()

            # Update subscriber stats
            self.subscriber.emails_opened += 1
            self.subscriber.last_opened = timezone.now()
            self.subscriber.save()

    def mark_clicked(self, link_url):
        if self.status != 'clicked':
            self.status = 'clicked'
            self.first_click_at = timezone.now()

            # Update newsletter stats
            self.newsletter.clicked_count += 1
            self.newsletter.save()

        self.click_count += 1
        if link_url not in self.clicked_links:
            self.clicked_links.append(link_url)
        self.save()

        # Update subscriber stats
        self.subscriber.links_clicked += 1
        self.subscriber.save()


class NewsletterTemplate(models.Model):
    """Reusable newsletter templates"""

    TEMPLATE_TYPE_CHOICES = [
        ('regular', 'Regular Newsletter'),
        ('digest', 'Digest'),
        ('event', 'Event Announcement'),
        ('special', 'Special Announcement'),
        ('promotional', 'Promotional'),
    ]

    # Core fields
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='regular')
    description = models.TextField(blank=True)

    # Template content
    html_template = models.TextField(help_text="HTML template with placeholders")
    text_template = models.TextField(help_text="Plain text template with placeholders")
    css_styles = models.TextField(blank=True, help_text="Custom CSS styles")

    # Sections
    has_header = models.BooleanField(default=True)
    has_footer = models.BooleanField(default=True)
    has_social_links = models.BooleanField(default=True)
    sections = models.JSONField(default=list, help_text="Available content sections")

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Created by
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        # Ensure only one default template per type
        if self.is_default:
            NewsletterTemplate.objects.filter(
                template_type=self.template_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"