from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
import uuid
from interactions.models import Like, Comment, Share, View, Bookmark


def news_image_path(instance, filename):
    """Generate path for news image uploads"""
    ext = filename.split('.')[-1]
    return f'news/{instance.article.id}/{uuid.uuid4()}.{ext}'


class NewsArticle(models.Model):
    """Enhanced news article model with Twitter-like features"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('rejected', 'Rejected'),
    ]

    # Content fields
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True, blank=True)
    summary = models.TextField(
        max_length=500, help_text="Brief summary of the article")
    content = models.TextField()

    # SEO fields
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    keywords = models.CharField(max_length=255, blank=True)

    # Categories and Tags
    category = models.ForeignKey(
        'tags.Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_articles'
    )
    tags = models.ManyToManyField(
        'tags.Tag',
        related_name='news_articles',
        blank=True
    )
    # Media
    featured_image = models.ImageField(
        upload_to='news/featured/', blank=True, null=True)
    image_caption = models.CharField(max_length=200, blank=True)
    image_credit = models.CharField(max_length=100, blank=True)

    # Metadata
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_articles'
    )
    source = models.CharField(
        max_length=200, blank=True, help_text="News source")
    source_url = models.URLField(blank=True, help_text="Original source URL")
    location = models.CharField(
        max_length=100, blank=True, help_text="Location of the news")

    # Status and visibility
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')
    is_breaking = models.BooleanField(
        default=False, help_text="Mark as breaking news")
    is_featured = models.BooleanField(
        default=False, help_text="Feature on homepage")
    is_trending = models.BooleanField(
        default=False, help_text="Show in trending section")
    is_exclusive = models.BooleanField(
        default=False, help_text="Exclusive content")

    # AI-generated content support
    is_ai_generated = models.BooleanField(default=False)
    ai_summary = models.TextField(blank=True, help_text="AI-generated summary")
    ai_tags_suggested = models.JSONField(default=list, blank=True)
    ai_confidence_score = models.FloatField(null=True, blank=True)

    # Twitter-like features - counts
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)

    # Generic relations for interactions
    likes = GenericRelation(Like)
    comments = GenericRelation(Comment)
    shares = GenericRelation(Share)
    views = GenericRelation(View)
    bookmarks = GenericRelation(Bookmark)

    # Publishing details
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_news'
    )
    rejection_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    breaking_expires_at = models.DateTimeField(null=True, blank=True)

    # Content settings
    allow_comments = models.BooleanField(default=True)
    require_comment_approval = models.BooleanField(default=False)

    class Meta:
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_breaking', '-published_at']),
            models.Index(fields=['is_featured', '-published_at']),
            models.Index(fields=['-views_count']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while NewsArticle.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Auto-expire breaking news after 24 hours
        if self.is_breaking and not self.breaking_expires_at:
            self.breaking_expires_at = timezone.now() + timezone.timedelta(hours=24)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('news:detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def get_reading_time(self):
        """Calculate estimated reading time"""
        word_count = len(self.content.split())
        minutes = word_count // 200  # Average reading speed
        return max(1, minutes)

    @property
    def is_new(self):
        """Check if article was published in last 24 hours"""
        if self.published_at:
            return timezone.now() - self.published_at < timezone.timedelta(hours=24)
        return False


class NewsImage(models.Model):
    """Gallery images for news articles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = models.ImageField(upload_to=news_image_path)
    caption = models.CharField(max_length=200, blank=True)
    credit = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.article.title}"


class NewsRevision(models.Model):
    """Track revisions of news articles for version control"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='revisions'
    )
    title = models.CharField(max_length=300)
    content = models.TextField()
    summary = models.TextField(max_length=500)
    revision_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    revision_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Revision of {self.article.title} at {self.created_at}"
