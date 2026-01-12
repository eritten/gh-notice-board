import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class Announcement(models.Model):
    """Enhanced public announcements model"""

    ANNOUNCEMENT_TYPE_CHOICES = [
        ('government', 'Government Notice'),
        ('public_service', 'Public Service'),
        ('emergency', 'Emergency Alert'),
        ('health', 'Health Advisory'),
        ('education', 'Education Notice'),
        ('community', 'Community Announcement'),
        ('legal', 'Legal Notice'),
        ('tender', 'Tender/Procurement'),
        ('policy', 'Policy Update'),
        ('infrastructure', 'Infrastructure Update'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    TARGET_AUDIENCE_CHOICES = [
        ('general', 'General Public'),
        ('students', 'Students'),
        ('businesses', 'Businesses'),
        ('farmers', 'Farmers'),
        ('health_workers', 'Health Workers'),
        ('teachers', 'Teachers'),
        ('diaspora', 'Diaspora'),
        ('specific_region', 'Specific Region'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    summary = models.CharField(max_length=500, help_text="Brief summary for listings")
    content = models.TextField(help_text="Full announcement content")

    # Categorization
    announcement_type = models.CharField(max_length=30, choices=ANNOUNCEMENT_TYPE_CHOICES)
    category = models.ForeignKey('tags.Category', on_delete=models.SET_NULL, null=True, related_name='announcements')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES, default='general')

    # Source and authority
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_announcements')
    source_organization = models.CharField(max_length=200)
    organization_logo = models.ImageField(upload_to='announcements/logos/', blank=True)
    organization_verified = models.BooleanField(default=False)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Official reference number")

    # Contact information
    contact_person = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)

    # Location targeting
    is_national = models.BooleanField(default=True, help_text="Applies to entire Ghana")
    regions = models.JSONField(default=list, blank=True, help_text="List of regions")
    districts = models.JSONField(default=list, blank=True, help_text="List of districts")
    location_details = models.TextField(blank=True)

    # Media and documents
    featured_image = models.ImageField(upload_to='announcements/featured/%Y/%m/', blank=True)
    document = models.FileField(upload_to='announcements/documents/%Y/%m/', blank=True)
    document_title = models.CharField(max_length=200, blank=True)
    video_url = models.URLField(blank=True, help_text="YouTube or other video URL")

    # Priority and visibility
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    is_emergency = models.BooleanField(default=False, help_text="Emergency alert requiring immediate attention")
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of lists")
    is_featured = models.BooleanField(default=False)

    # Scheduling and expiry
    publish_at = models.DateTimeField(blank=True, null=True, help_text="Schedule for future publication")
    expires_at = models.DateTimeField(blank=True, null=True, help_text="When announcement expires")

    # Legal and compliance
    requires_acknowledgment = models.BooleanField(default=False)
    legal_disclaimer = models.TextField(blank=True)
    related_law = models.CharField(max_length=300, blank=True, help_text="Related law or regulation")

    # Actions
    action_required = models.BooleanField(default=False)
    action_deadline = models.DateTimeField(blank=True, null=True)
    action_url = models.URLField(blank=True, help_text="URL for required action")
    action_instructions = models.TextField(blank=True)

    # AI Integration
    is_ai_translated = models.BooleanField(default=False)
    ai_translations = models.JSONField(default=dict, blank=True, help_text="Translations in local languages")
    ai_summary = models.TextField(blank=True, help_text="AI-generated summary")
    ai_keywords = models.TextField(blank=True, help_text="AI-extracted keywords")

    # Engagement tracking
    views_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    acknowledgments_count = models.PositiveIntegerField(default=0)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approval_notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_announcements'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    last_promoted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-is_emergency', '-is_pinned', '-priority', '-published_at']
        indexes = [
            models.Index(fields=['announcement_type', 'status']),
            models.Index(fields=['is_emergency', 'is_pinned']),
            models.Index(fields=['slug']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['target_audience']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Announcement.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        # Auto-publish if scheduled
        if self.publish_at and timezone.now() >= self.publish_at:
            self.status = 'published'
            self.published_at = self.publish_at

        # Auto-expire if past expiry
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'

        # Set published_at when first published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"

    @property
    def is_active(self):
        now = timezone.now()
        return (
            self.status == 'published' and
            (not self.expires_at or self.expires_at > now) and
            (not self.publish_at or self.publish_at <= now)
        )

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    @property
    def days_until_expiry(self):
        if not self.expires_at:
            return None
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return delta.days

    @property
    def requires_action(self):
        return self.action_required and self.action_deadline

    @property
    def action_overdue(self):
        return self.action_deadline and timezone.now() > self.action_deadline

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


class AnnouncementImage(models.Model):
    """Additional images for announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='announcements/gallery/%Y/%m/')
    caption = models.CharField(max_length=300, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.announcement.title}"


class AnnouncementAcknowledgment(models.Model):
    """Track user acknowledgments of important announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='acknowledgments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcement_acknowledgments')
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        unique_together = ['announcement', 'user']
        indexes = [
            models.Index(fields=['announcement', 'user']),
        ]

    def __str__(self):
        return f"{self.user.get_display_name()} acknowledged {self.announcement.title}"


class AnnouncementTranslation(models.Model):
    """Translations for announcements in local languages"""
    LANGUAGE_CHOICES = [
        ('tw', 'Twi'),
        ('ee', 'Ewe'),
        ('ga', 'Ga'),
        ('dag', 'Dagbani'),
        ('ha', 'Hausa'),
        ('nz', 'Nzema'),
    ]

    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=3, choices=LANGUAGE_CHOICES)
    title = models.CharField(max_length=300)
    summary = models.CharField(max_length=500)
    content = models.TextField()
    is_machine_translated = models.BooleanField(default=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_translations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['announcement', 'language']

    def __str__(self):
        return f"{self.announcement.title} - {self.get_language_display()}"


class AnnouncementAlert(models.Model):
    """SMS/Email alerts for critical announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='alerts')

    # Alert details
    alert_type = models.CharField(max_length=10, choices=[('sms', 'SMS'), ('email', 'Email')])
    recipient_count = models.PositiveIntegerField(default=0)
    message = models.TextField()

    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    failed_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.get_alert_type_display()} alert for {self.announcement.title}"