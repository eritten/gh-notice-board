import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class EventCategory(models.Model):
    """Category for events"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Event Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    """Enhanced event model with comprehensive features"""

    EVENT_TYPE_CHOICES = [
        ('in-person', 'In Person'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
        ('completed', 'Completed'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    summary = models.CharField(max_length=500, help_text="Brief description for listings")
    description = models.TextField(help_text="Full event description with rich text")
    agenda = models.TextField(blank=True, help_text="Event schedule and agenda")

    # Categorization
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')

    # Event details
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='in-person')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='Africa/Accra')

    # Venue information
    venue_name = models.CharField(max_length=300)
    venue_address = models.TextField()
    venue_details = models.TextField(blank=True, help_text="Additional venue information")
    venue_map_url = models.URLField(blank=True)

    # Virtual event fields
    virtual_meeting_url = models.URLField(blank=True)
    virtual_meeting_password = models.CharField(max_length=100, blank=True)

    # Media
    featured_image = models.ImageField(upload_to='events/featured/%Y/%m/', blank=True)

    # Organizer and contact
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organized_events')
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    website_url = models.URLField(blank=True)

    # Registration
    registration_required = models.BooleanField(default=True)
    registration_url = models.URLField(blank=True, help_text="External registration link")
    registration_deadline = models.DateTimeField(blank=True, null=True)
    max_attendees = models.PositiveIntegerField(default=0, help_text="0 for unlimited")
    registered_count = models.PositiveIntegerField(default=0)
    allow_waitlist = models.BooleanField(default=True)
    waitlist_count = models.PositiveIntegerField(default=0)
    registration_instructions = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='GHS')
    early_bird_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    early_bird_deadline = models.DateTimeField(blank=True, null=True)

    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)

    # Engagement tracking
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)

    # Additional information
    cancellation_policy = models.TextField(blank=True)
    covid_safety_measures = models.TextField(blank=True)
    parking_info = models.TextField(blank=True)
    accessibility_info = models.TextField(blank=True)

    # Social media
    facebook_event_url = models.URLField(blank=True)
    twitter_hashtag = models.CharField(max_length=100, blank=True)
    livestream_url = models.URLField(blank=True)

    # Internal use
    check_in_code = models.CharField(max_length=20, blank=True, help_text="QR code for check-in")
    certificate_template = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['start_date', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['organizer']),
            models.Index(fields=['is_featured', 'is_trending']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        # Set published_at when first published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.price == 0

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now() and not self.is_cancelled

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and not self.is_cancelled

    @property
    def is_past(self):
        return self.end_date < timezone.now()

    def days_until_event(self):
        if self.is_past:
            return 0
        delta = self.start_date - timezone.now()
        return delta.days

    def is_full(self):
        if self.max_attendees == 0:
            return False
        return self.registered_count >= self.max_attendees

    def available_spots(self):
        if self.max_attendees == 0:
            return float('inf')
        return max(0, self.max_attendees - self.registered_count)


class EventSpeaker(models.Model):
    """Speakers for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='speakers')
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    bio = models.TextField()
    photo = models.ImageField(upload_to='events/speakers/', blank=True)

    # Social links
    linkedin_url = models.URLField(blank=True)
    twitter_username = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.event.title}"


class EventSponsor(models.Model):
    """Sponsors for events"""
    SPONSORSHIP_LEVELS = [
        ('title', 'Title Sponsor'),
        ('platinum', 'Platinum'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('bronze', 'Bronze'),
        ('partner', 'Partner'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sponsors')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='events/sponsors/')
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    sponsorship_level = models.CharField(max_length=20, choices=SPONSORSHIP_LEVELS, default='partner')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'sponsorship_level', 'name']

    def __str__(self):
        return f"{self.name} - {self.event.title}"


class EventImage(models.Model):
    """Gallery images for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='events/gallery/%Y/%m/')
    caption = models.CharField(max_length=300, blank=True)
    is_cover = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.event.title}"


class EventRegistration(models.Model):
    """User registrations for events"""

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('waitlisted', 'Waitlisted'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    REGISTRATION_TYPES = [
        ('regular', 'Regular'),
        ('early_bird', 'Early Bird'),
        ('vip', 'VIP'),
        ('student', 'Student'),
        ('group', 'Group'),
        ('complimentary', 'Complimentary'),
    ]

    ATTENDANCE_STATUS = [
        ('not_checked_in', 'Not Checked In'),
        ('checked_in', 'Checked In'),
        ('no_show', 'No Show'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    registration_type = models.CharField(max_length=20, choices=REGISTRATION_TYPES, default='regular')
    ticket_number = models.CharField(max_length=50, unique=True)

    # Payment
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='not_checked_in')
    checked_in_at = models.DateTimeField(blank=True, null=True)

    # Additional info
    special_requirements = models.TextField(blank=True, help_text="Dietary, accessibility needs, etc.")
    accept_terms = models.BooleanField(default=False)

    # Flags
    is_speaker = models.BooleanField(default=False)
    is_vip = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['ticket_number']),
        ]

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.event.title}"


class EventReminder(models.Model):
    """Reminders for event attendees"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    send_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['send_at']

    def __str__(self):
        return f"Reminder: {self.subject} for {self.event.title}"
