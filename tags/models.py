from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    """Main categories for content organization"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    color = models.CharField(max_length=7, default='#000000', help_text="Hex color code")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'order']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tags for content classification"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tags'
    )

    # Popularity tracking
    usage_count = models.PositiveIntegerField(default=0, help_text="Number of times used")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-usage_count']),
            models.Index(fields=['category', '-usage_count']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def increment_usage(self):
        """Increment usage count when tag is used"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    def __str__(self):
        return self.name


class SubTag(models.Model):
    """Sub-tags for more specific classification under main tags"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    parent_tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='subtags'
    )

    # Popularity tracking
    usage_count = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        unique_together = ['parent_tag', 'slug']
        indexes = [
            models.Index(fields=['parent_tag', '-usage_count']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def increment_usage(self):
        """Increment usage count when subtag is used"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    def __str__(self):
        return f"{self.parent_tag.name} > {self.name}"


class UserSubscription(models.Model):
    """User subscriptions to categories, tags, and subtags"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')

    # What to subscribe to
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    subtag = models.ForeignKey(
        SubTag,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribers'
    )

    # Notification preferences
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
        ],
        default='instant'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'tag']),
            models.Index(fields=['user', 'push_notifications']),
        ]
        # Ensure user can't subscribe to same thing twice
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category'],
                name='unique_user_category_subscription',
                condition=models.Q(category__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['user', 'tag'],
                name='unique_user_tag_subscription',
                condition=models.Q(tag__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['user', 'subtag'],
                name='unique_user_subtag_subscription',
                condition=models.Q(subtag__isnull=False)
            ),
        ]

    def __str__(self):
        if self.category:
            return f"{self.user.username} subscribed to category: {self.category.name}"
        elif self.tag:
            return f"{self.user.username} subscribed to tag: {self.tag.name}"
        elif self.subtag:
            return f"{self.user.username} subscribed to subtag: {self.subtag.name}"
        return f"{self.user.username} subscription"


class PushSubscription(models.Model):
    """Store push notification subscription data for Web Push API"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_subscriptions')

    # Push subscription data
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)  # Public key
    auth = models.CharField(max_length=255)     # Auth secret

    # Device/Browser info
    user_agent = models.TextField(blank=True)
    device_name = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"Push subscription for {self.user.username}"


class UserInterest(models.Model):
    """Track user interests for algorithm-based recommendations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interests')

    # Interest tracking
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Interest score (calculated based on user interactions)
    score = models.FloatField(default=0.0, help_text="Interest score based on interactions")

    # Interaction counts
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    time_spent = models.PositiveIntegerField(default=0, help_text="Total seconds spent on content")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score']
        unique_together = [
            ['user', 'category'],
            ['user', 'tag'],
        ]
        indexes = [
            models.Index(fields=['user', '-score']),
        ]

    def calculate_score(self):
        """Calculate interest score based on interactions"""
        # Weighted scoring
        score = (
            (self.view_count * 1) +
            (self.like_count * 5) +
            (self.share_count * 10) +
            (self.time_spent / 60 * 2)  # Convert seconds to minutes, weight by 2
        )
        self.score = score
        self.save(update_fields=['score'])
        return score

    def __str__(self):
        target = self.category.name if self.category else self.tag.name
        return f"{self.user.username} interested in {target} (score: {self.score})"
