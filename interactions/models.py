from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Like(models.Model):
    """Generic like model for any content type"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='likes')

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.content_object}"


class Dislike(models.Model):
    """Generic dislike model for any content type"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='dislikes')

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} dislikes {self.content_object}"


class Review(models.Model):
    """Generic review/rating model for any content type"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='reviews')

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    # Review fields
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()

    # Status
    is_approved = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.rating}★ review"


class Bookmark(models.Model):
    """Allow users to bookmark/save content for later"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='bookmarks')

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} bookmarked {self.content_object}"


class Share(models.Model):
    """Twitter-like share/retweet functionality"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='shares')

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    # Share details
    comment = models.TextField(
        blank=True, help_text="Optional comment when sharing")
    is_quote = models.BooleanField(
        default=False, help_text="True if this is a quote share")

    # Share tracking
    share_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        action = "quote shared" if self.is_quote else "shared"
        return f"{self.user.username} {action} {self.content_object}"


class Comment(models.Model):
    """Threaded comments for any content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='comments')

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    # Comment content
    content = models.TextField()

    # Threading support
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    # Metadata
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)

    # Interaction counts
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.content_object}"

    def save(self, *args, **kwargs):
        if self.pk and self.content != self._state.fields_cache.get('content'):
            self.is_edited = True
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)

        # Update reply count on parent
        if self.parent:
            self.parent.reply_count = self.parent.replies.count()
            self.parent.save(update_fields=['reply_count'])


class View(models.Model):
    """Track content views for analytics"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='views',
        null=True,  # Allow anonymous views
        blank=True
    )

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    # View details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)

    # Time tracking
    duration = models.PositiveIntegerField(
        default=0,
        help_text="View duration in seconds"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        viewer = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{viewer} viewed {self.content_object}"


class Report(models.Model):
    """User reports for content moderation"""
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Support both int and UUID
    content_object = GenericForeignKey('content_type', 'object_id')

    # Report details
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('misinformation', 'Misinformation'),
        ('inappropriate', 'Inappropriate Content'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other'),
    ]

    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(
        help_text="Additional details about the report")

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    # Moderation
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interaction_reports_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    moderator_notes = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['reporter']),
        ]

    def __str__(self):
        return f"Report: {self.reason} - {self.status}"
