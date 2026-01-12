import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class DiasporaPost(models.Model):
    """Enhanced diaspora content and community hub"""

    CONTENT_TYPE_CHOICES = [
        ('news', 'News'),
        ('story', 'Success Story'),
        ('interview', 'Interview'),
        ('immigration', 'Immigration Update'),
        ('embassy', 'Embassy Notice'),
        ('community', 'Community Network'),
        ('event', 'Diaspora Event'),
        ('investment', 'Investment Opportunity'),
        ('cultural', 'Cultural Preservation'),
        ('homecoming', 'Homecoming Story'),
        ('advice', 'Expert Advice'),
        ('partnership', 'Partnership'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('featured', 'Featured'),
        ('archived', 'Archived'),
    ]

    REGION_CHOICES = [
        ('north-america', 'North America'),
        ('europe', 'Europe'),
        ('asia', 'Asia'),
        ('africa', 'Africa'),
        ('south-america', 'South America'),
        ('oceania', 'Oceania'),
        ('middle-east', 'Middle East'),
        ('global', 'Global'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    summary = models.CharField(max_length=500, help_text="Brief summary for listings")
    content = models.TextField(help_text="Full content with rich text")

    # Content categorization
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    category = models.ForeignKey('tags.Category', on_delete=models.SET_NULL, null=True, related_name='diaspora_posts')

    # Author and source
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diaspora_posts')
    is_diaspora_author = models.BooleanField(default=True, help_text="Is the author from diaspora")

    # Location details
    region = models.CharField(max_length=20, choices=REGION_CHOICES, default='global')
    country = models.CharField(max_length=100, help_text="Specific country")
    city = models.CharField(max_length=100, blank=True)
    diaspora_community = models.CharField(max_length=200, blank=True, help_text="Name of diaspora community")

    # Organization details
    organization_name = models.CharField(max_length=200, blank=True)
    organization_type = models.CharField(max_length=100, blank=True, help_text="Embassy, Association, Business, etc.")
    organization_logo = models.ImageField(upload_to='diaspora/logos/', blank=True)
    organization_verified = models.BooleanField(default=False)

    # Media
    featured_image = models.ImageField(upload_to='diaspora/featured/%Y/%m/', blank=True)
    featured_video_url = models.URLField(blank=True, help_text="YouTube or other video URL")

    # Contact information
    contact_person = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    website_url = models.URLField(blank=True)
    social_media_links = models.JSONField(default=dict, blank=True)

    # Engagement features
    allow_comments = models.BooleanField(default=True)
    allow_sharing = models.BooleanField(default=True)
    requires_membership = models.BooleanField(default=False, help_text="Requires diaspora membership to view full content")

    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False, help_text="Urgent notice")
    is_pinned = models.BooleanField(default=False, help_text="Pin to top")

    # Investment/Partnership specific
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    investment_currency = models.CharField(max_length=3, default='USD', blank=True)
    partnership_type = models.CharField(max_length=100, blank=True)
    opportunity_deadline = models.DateTimeField(blank=True, null=True)

    # Event specific
    event_date = models.DateTimeField(blank=True, null=True)
    event_location = models.CharField(max_length=300, blank=True)
    event_registration_url = models.URLField(blank=True)

    # AI Integration
    is_ai_translated = models.BooleanField(default=False)
    ai_translations = models.JSONField(default=dict, blank=True)
    ai_summary = models.TextField(blank=True, help_text="AI-generated summary")
    ai_tags = models.TextField(blank=True)

    # Engagement tracking
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-is_urgent', '-is_pinned', '-published_at']
        indexes = [
            models.Index(fields=['content_type', 'status']),
            models.Index(fields=['region', 'country']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', 'is_trending']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while DiasporaPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        # Set published_at when first published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.country}"

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    @property
    def is_active(self):
        return self.status in ['published', 'featured']

    @property
    def is_event(self):
        return self.content_type == 'event' and self.event_date

    @property
    def is_upcoming_event(self):
        return self.is_event and self.event_date and self.event_date > timezone.now()

    @property
    def is_investment_opportunity(self):
        return self.content_type == 'investment' and self.investment_amount


class DiasporaImage(models.Model):
    """Gallery images for diaspora posts"""
    post = models.ForeignKey(DiasporaPost, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='diaspora/gallery/%Y/%m/')
    caption = models.CharField(max_length=300, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.post.title}"


class DiasporaNetwork(models.Model):
    """Diaspora professional and social networks"""

    NETWORK_TYPE_CHOICES = [
        ('professional', 'Professional Network'),
        ('alumni', 'Alumni Association'),
        ('hometown', 'Hometown Association'),
        ('religious', 'Religious Group'),
        ('cultural', 'Cultural Association'),
        ('business', 'Business Network'),
        ('social', 'Social Club'),
        ('women', 'Women\'s Group'),
        ('youth', 'Youth Organization'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    mission = models.TextField(blank=True)

    # Network details
    network_type = models.CharField(max_length=20, choices=NETWORK_TYPE_CHOICES)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True)

    # Location
    based_in_country = models.CharField(max_length=100)
    based_in_city = models.CharField(max_length=100)
    chapters = models.JSONField(default=list, blank=True, help_text="List of chapter locations")

    # Leadership
    president_name = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    office_address = models.TextField(blank=True)

    # Online presence
    website_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    linkedin_url = models.URLField(blank=True)
    whatsapp_group = models.CharField(max_length=100, blank=True)

    # Membership
    membership_count = models.PositiveIntegerField(default=0)
    membership_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    membership_currency = models.CharField(max_length=3, default='USD')
    membership_requirements = models.TextField(blank=True)

    # Logo and media
    logo = models.ImageField(upload_to='diaspora/networks/logos/', blank=True)
    cover_image = models.ImageField(upload_to='diaspora/networks/covers/', blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_networks'
    )
    verified_at = models.DateTimeField(blank=True, null=True)

    # Activity
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    events_count = models.PositiveIntegerField(default=0)
    projects_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_networks'
    )

    class Meta:
        ordering = ['-is_verified', '-membership_count', 'name']
        indexes = [
            models.Index(fields=['network_type', 'based_in_country']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_verified', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.based_in_country}"


class DiasporaDirectory(models.Model):
    """Directory of diaspora professionals and businesses"""

    DIRECTORY_TYPE_CHOICES = [
        ('professional', 'Professional'),
        ('business', 'Business'),
        ('service', 'Service Provider'),
        ('consultant', 'Consultant'),
        ('organization', 'Organization'),
    ]

    PROFESSION_CHOICES = [
        ('doctor', 'Medical Doctor'),
        ('nurse', 'Nurse'),
        ('engineer', 'Engineer'),
        ('teacher', 'Teacher/Educator'),
        ('lawyer', 'Lawyer'),
        ('accountant', 'Accountant'),
        ('it', 'IT Professional'),
        ('entrepreneur', 'Entrepreneur'),
        ('academic', 'Academic/Researcher'),
        ('artist', 'Artist/Creative'),
        ('other', 'Other'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diaspora_listings'
    )
    listing_type = models.CharField(max_length=20, choices=DIRECTORY_TYPE_CHOICES)

    # Professional details
    full_name = models.CharField(max_length=200)
    professional_title = models.CharField(max_length=200)
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES)
    specialization = models.CharField(max_length=200)
    years_experience = models.PositiveIntegerField()

    # Business details
    business_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=200, blank=True)
    services_offered = models.TextField()

    # Location
    current_country = models.CharField(max_length=100)
    current_city = models.CharField(max_length=100)
    origin_region = models.CharField(max_length=100, help_text="Region in Ghana")

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)

    # Professional info
    qualifications = models.TextField()
    certifications = models.TextField(blank=True)
    languages = models.CharField(max_length=200)
    availability = models.CharField(max_length=100, blank=True, help_text="e.g., 'Available for consultancy'")

    # Media
    profile_photo = models.ImageField(upload_to='diaspora/directory/profiles/', blank=True)
    business_logo = models.ImageField(upload_to='diaspora/directory/logos/', blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verification_documents = models.FileField(upload_to='diaspora/directory/docs/', blank=True)

    # Visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    allow_contact = models.BooleanField(default=True)

    # Stats
    profile_views = models.PositiveIntegerField(default=0)
    contact_requests = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-is_verified', '-created_at']
        indexes = [
            models.Index(fields=['listing_type', 'profession']),
            models.Index(fields=['current_country', 'current_city']),
            models.Index(fields=['is_verified', 'is_active']),
        ]

    def __str__(self):
        if self.business_name:
            return f"{self.business_name} - {self.current_country}"
        return f"{self.full_name} - {self.professional_title}"

    def increment_views(self):
        self.profile_views += 1
        self.save(update_fields=['profile_views'])


class DiasporaInvestment(models.Model):
    """Investment opportunities and partnerships for diaspora"""

    INVESTMENT_TYPE_CHOICES = [
        ('real-estate', 'Real Estate'),
        ('business', 'Business Partnership'),
        ('agriculture', 'Agriculture'),
        ('technology', 'Technology'),
        ('manufacturing', 'Manufacturing'),
        ('education', 'Education'),
        ('healthcare', 'Healthcare'),
        ('infrastructure', 'Infrastructure'),
        ('social', 'Social Enterprise'),
    ]

    INVESTMENT_STAGE_CHOICES = [
        ('idea', 'Idea Stage'),
        ('startup', 'Startup'),
        ('growth', 'Growth Stage'),
        ('expansion', 'Expansion'),
        ('established', 'Established'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    summary = models.CharField(max_length=500)
    description = models.TextField()

    # Investment details
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPE_CHOICES)
    investment_stage = models.CharField(max_length=20, choices=INVESTMENT_STAGE_CHOICES)
    sector = models.CharField(max_length=100)

    # Financial details
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_investment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    expected_return = models.CharField(max_length=100, blank=True)
    payback_period = models.CharField(max_length=100, blank=True)

    # Location
    location_country = models.CharField(max_length=100, default='Ghana')
    location_region = models.CharField(max_length=100)
    location_city = models.CharField(max_length=100)

    # Company/Project details
    company_name = models.CharField(max_length=200)
    company_registration = models.CharField(max_length=100, blank=True)
    established_year = models.PositiveIntegerField(blank=True, null=True)
    team_size = models.PositiveIntegerField(blank=True, null=True)

    # Contact
    contact_person = models.CharField(max_length=200)
    contact_title = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)

    # Documents and media
    business_plan = models.FileField(upload_to='diaspora/investments/plans/', blank=True)
    financial_projections = models.FileField(upload_to='diaspora/investments/financials/', blank=True)
    pitch_deck = models.FileField(upload_to='diaspora/investments/pitches/', blank=True)
    featured_image = models.ImageField(upload_to='diaspora/investments/images/', blank=True)

    # Due diligence
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
    risk_assessment = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    deadline = models.DateTimeField(blank=True, null=True)

    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    inquiries_count = models.PositiveIntegerField(default=0)

    # Relations
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_investments'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-is_featured', '-published_at']
        indexes = [
            models.Index(fields=['investment_type', 'investment_stage']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_verified', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_active and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.get_investment_type_display()}"

    @property
    def is_deadline_passed(self):
        return self.deadline and timezone.now() > self.deadline