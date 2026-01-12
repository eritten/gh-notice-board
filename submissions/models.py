import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class ContentSubmission(models.Model):
    """Enhanced user submissions for content"""

    SUBMISSION_TYPE_CHOICES = [
        ('news', 'News Tip'),
        ('event', 'Event Submission'),
        ('announcement', 'Announcement'),
        ('opportunity', 'Opportunity'),
        ('diaspora', 'Diaspora Story'),
        ('report', 'Investigative Report'),
        ('opinion', 'Opinion Piece'),
        ('press-release', 'Press Release'),
        ('community', 'Community News'),
        ('photo', 'Photo Story'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_type = models.CharField(
        max_length=20, choices=SUBMISSION_TYPE_CHOICES)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    summary = models.CharField(
        max_length=500, help_text="Brief summary", default="")
    content = models.TextField(help_text="Full content")

    # Submitter information
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='content_submissions'
    )
    submitter_name = models.CharField(max_length=200)
    submitter_email = models.EmailField()
    submitter_phone = models.CharField(max_length=20, blank=True)
    submitter_organization = models.CharField(max_length=200, blank=True)
    submitter_location = models.CharField(max_length=200, blank=True)

    # Additional information
    location = models.CharField(
        max_length=200, blank=True, help_text="Location relevant to submission")
    event_date = models.DateTimeField(blank=True, null=True)
    tags = models.TextField(blank=True, help_text="Comma-separated tags")
    sources = models.TextField(blank=True, help_text="Sources or references")
    additional_info = models.JSONField(default=dict, blank=True)

    # Media uploads
    featured_image = models.ImageField(
        upload_to='submissions/images/%Y/%m/', blank=True)
    document = models.FileField(
        upload_to='submissions/documents/%Y/%m/', blank=True)
    document_title = models.CharField(max_length=200, blank=True)
    additional_images = models.JSONField(
        default=list, blank=True, help_text="URLs of additional images")

    # Priority and visibility
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_anonymous = models.BooleanField(
        default=False, help_text="Hide submitter identity")
    is_exclusive = models.BooleanField(
        default=False, help_text="Exclusive content")
    requires_fact_check = models.BooleanField(default=False)

    # Review process
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='submitted')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions'
    )
    reviewer_notes = models.TextField(
        blank=True, help_text="Internal notes for reviewers")
    rejection_reason = models.TextField(blank=True)
    fact_check_notes = models.TextField(blank=True)

    # Publication details
    published_as_type = models.CharField(
        max_length=20, blank=True, help_text="Content type when published")
    published_as_id = models.UUIDField(
        blank=True, null=True, help_text="ID of published content")
    published_url = models.URLField(blank=True)

    # Compensation
    compensation_offered = models.BooleanField(default=False)
    compensation_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, blank=True)
    payment_notes = models.TextField(blank=True)

    # Legal
    copyright_agreement = models.BooleanField(default=False)
    verification_consent = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # Engagement tracking
    views_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission_type', 'status']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while ContentSubmission.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        # Set submitted_at when status changes to submitted
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_submission_type_display()} - {self.title}"

    def approve(self, user):
        """Approve the submission"""
        self.status = 'approved'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, user, reason):
        """Reject the submission"""
        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    @property
    def is_pending(self):
        return self.status in ['submitted', 'under_review']

    @property
    def can_edit(self):
        return self.status in ['draft', 'rejected']


class ContactMessage(models.Model):
    """Enhanced contact form submissions"""

    INQUIRY_TYPE_CHOICES = [
        ('general', 'General Inquiry'),
        ('feedback', 'Feedback'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('partnership', 'Partnership Proposal'),
        ('advertising', 'Advertising Inquiry'),
        ('press', 'Press Inquiry'),
        ('technical', 'Technical Issue'),
        ('content', 'Content Related'),
        ('other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inquiry_type = models.CharField(
        max_length=20, choices=INQUIRY_TYPE_CHOICES, default='general')
    subject = models.CharField(max_length=300)
    message = models.TextField()

    # Sender information
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_messages'
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)

    # Additional details
    referrer = models.CharField(
        max_length=200, blank=True, help_text="How they found us")
    attachment = models.FileField(
        upload_to='contact/attachments/%Y/%m/', blank=True)

    # Status and handling
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    is_responded = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_messages'
    )

    # Response tracking
    response_notes = models.TextField(blank=True)
    response_sent_at = models.DateTimeField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)

    # Technical info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Contact Messages"
        indexes = [
            models.Index(fields=['inquiry_type', 'is_resolved']),
            models.Index(fields=['priority', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_inquiry_type_display()}: {self.subject}"

    def mark_read(self, user=None):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            if user:
                self.assigned_to = user
            self.save()

    def mark_responded(self, notes=''):
        self.is_responded = True
        self.responded_at = timezone.now()
        if notes:
            self.response_notes = notes
        self.save()

    def mark_resolved(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()


class FeedbackSubmission(models.Model):
    """User feedback and ratings"""

    FEEDBACK_TYPE_CHOICES = [
        ('feature', 'Feature Request'),
        ('bug', 'Bug Report'),
        ('improvement', 'Improvement Suggestion'),
        ('compliment', 'Compliment'),
        ('complaint', 'Complaint'),
        ('content', 'Content Feedback'),
        ('ui', 'UI/UX Feedback'),
    ]

    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback_type = models.CharField(
        max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # User and context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_submissions'
    )
    page_url = models.URLField(
        blank=True, help_text="Page where feedback was given")
    content_type = models.CharField(max_length=50, blank=True)
    content_id = models.UUIDField(blank=True, null=True)

    # Rating
    overall_rating = models.IntegerField(
        choices=RATING_CHOICES, blank=True, null=True)
    ease_of_use_rating = models.IntegerField(
        choices=RATING_CHOICES, blank=True, null=True)
    content_quality_rating = models.IntegerField(
        choices=RATING_CHOICES, blank=True, null=True)
    would_recommend = models.BooleanField(blank=True, null=True)

    # Additional info
    browser = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    screenshot = models.ImageField(
        upload_to='feedback/screenshots/%Y/%m/', blank=True)

    # Status
    is_reviewed = models.BooleanField(default=False)
    is_implemented = models.BooleanField(default=False)
    is_public = models.BooleanField(
        default=False, help_text="Show in public feedback section")

    # Response
    admin_response = models.TextField(blank=True)
    implementation_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    implemented_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback_type', 'is_reviewed']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_feedback_type_display()}: {self.title}"

    @property
    def average_rating(self):
        ratings = [r for r in [
            self.overall_rating,
            self.ease_of_use_rating,
            self.content_quality_rating
        ] if r is not None]
        return sum(ratings) / len(ratings) if ratings else None


class ReportSubmission(models.Model):
    """Content and user report submissions"""

    REPORT_TYPE_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('misinformation', 'Misinformation'),
        ('copyright', 'Copyright Violation'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('adult', 'Adult Content'),
        ('scam', 'Scam/Fraud'),
        ('other', 'Other'),
    ]

    REPORT_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('valid', 'Valid Report'),
        ('invalid', 'Invalid Report'),
        ('resolved', 'Resolved'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField()

    # What is being reported
    reported_content_type = models.CharField(max_length=50)
    reported_content_id = models.UUIDField()
    reported_content_url = models.URLField(blank=True)
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_against',
        blank=True,
        null=True
    )

    # Reporter
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_submitted'
    )

    # Evidence
    screenshot = models.ImageField(
        upload_to='reports/screenshots/%Y/%m/', blank=True)
    additional_info = models.TextField(blank=True)

    # Review process
    status = models.CharField(
        max_length=20, choices=REPORT_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_reviewed'
    )
    reviewer_notes = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(
                fields=['reported_content_type', 'reported_content_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.reported_content_type}"
