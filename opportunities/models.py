import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class Opportunity(models.Model):
    """Enhanced opportunities model for jobs, scholarships, grants, etc."""

    OPPORTUNITY_TYPE_CHOICES = [
        ('job', 'Job'),
        ('scholarship', 'Scholarship'),
        ('grant', 'Grant'),
        ('internship', 'Internship'),
        ('fellowship', 'Fellowship'),
        ('volunteer', 'Volunteer'),
        ('business', 'Business Opportunity'),
        ('funding', 'Funding'),
        ('mentorship', 'Mentorship'),
        ('training', 'Training/Workshop'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('expired', 'Expired'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('temporary', 'Temporary'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
        ('internship', 'Internship'),
        ('no-experience', 'No Experience Required'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    summary = models.CharField(max_length=500, help_text="Brief description for listings")
    description = models.TextField(help_text="Full description with requirements and benefits")

    # Categorization
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPE_CHOICES)
    category = models.ForeignKey('tags.Category', on_delete=models.SET_NULL, null=True, related_name='opportunities')

    # Organization details
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_opportunities')
    organization_name = models.CharField(max_length=200)
    organization_logo = models.ImageField(upload_to='opportunities/logos/', blank=True)
    organization_website = models.URLField(blank=True)
    organization_description = models.TextField(blank=True)
    organization_verified = models.BooleanField(default=False)

    # Location details
    location = models.CharField(max_length=200)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Ghana')
    is_remote = models.BooleanField(default=False)
    is_diaspora = models.BooleanField(default=False, help_text="Opportunity for diaspora")
    relocation_assistance = models.BooleanField(default=False)

    # Job-specific fields
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='GHS')
    show_salary = models.BooleanField(default=True)
    benefits = models.TextField(blank=True, help_text="List of benefits")

    # Requirements
    education_requirement = models.TextField(blank=True)
    experience_requirement = models.TextField(blank=True)
    skills_required = models.TextField(blank=True)
    languages_required = models.TextField(blank=True)
    certifications_required = models.TextField(blank=True)

    # Scholarship/Grant-specific fields
    funding_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    funding_currency = models.CharField(max_length=3, default='GHS', blank=True)
    duration = models.CharField(max_length=100, blank=True, help_text="Duration of opportunity")
    eligibility_criteria = models.TextField(blank=True)
    selection_process = models.TextField(blank=True)
    number_of_slots = models.PositiveIntegerField(default=1)

    # Application details
    application_method = models.CharField(max_length=50, default='external')  # external, email, platform
    application_url = models.URLField(blank=True)
    application_email = models.EmailField(blank=True)
    application_instructions = models.TextField(blank=True)
    required_documents = models.TextField(blank=True, help_text="List of required documents")
    deadline = models.DateTimeField(blank=True, null=True)

    # Contact information
    contact_person = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    # Media
    featured_image = models.ImageField(upload_to='opportunities/featured/%Y/%m/', blank=True)

    # AI Integration
    is_ai_enhanced = models.BooleanField(default=False)
    ai_match_keywords = models.TextField(blank=True, help_text="AI-generated keywords for matching")
    ai_summary = models.TextField(blank=True, help_text="AI-generated summary")

    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)

    # Engagement tracking
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-is_urgent', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['opportunity_type', 'status']),
            models.Index(fields=['deadline']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', 'is_trending']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Opportunity.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        # Set published_at when first published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Auto-expire if deadline passed
        if self.deadline and timezone.now() > self.deadline:
            self.status = 'expired'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_opportunity_type_display()} - {self.title}"

    @property
    def is_active(self):
        return self.status == 'published' and (not self.deadline or self.deadline > timezone.now())

    @property
    def days_until_deadline(self):
        if not self.deadline:
            return None
        if self.deadline < timezone.now():
            return 0
        delta = self.deadline - timezone.now()
        return delta.days

    @property
    def salary_range(self):
        if not self.show_salary or not self.salary_min:
            return "Not specified"
        if self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
        return f"{self.salary_currency} {self.salary_min:,.0f}+"

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_applications(self):
        self.applications_count += 1
        self.save(update_fields=['applications_count'])


class OpportunityImage(models.Model):
    """Additional images for opportunities"""
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='opportunities/gallery/%Y/%m/')
    caption = models.CharField(max_length=300, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.opportunity.title}"


class Application(models.Model):
    """Applications for opportunities"""

    APPLICATION_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='opportunity_applications')

    # Personal information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=200)

    # Application documents
    cv_file = models.FileField(upload_to='applications/cvs/%Y/%m/', blank=True)
    cover_letter = models.TextField()
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Additional information
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    current_position = models.CharField(max_length=200, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    availability = models.CharField(max_length=100, blank=True)
    references = models.TextField(blank=True)

    # Status tracking
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='draft')
    reviewer_notes = models.TextField(blank=True)
    interview_date = models.DateTimeField(blank=True, null=True)
    interview_location = models.CharField(max_length=300, blank=True)
    interview_notes = models.TextField(blank=True)

    # AI matching
    ai_match_score = models.FloatField(blank=True, null=True)
    ai_match_reasons = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['opportunity', 'applicant']
        indexes = [
            models.Index(fields=['opportunity', 'status']),
            models.Index(fields=['applicant']),
        ]

    def __str__(self):
        return f"Application from {self.full_name} for {self.opportunity.title}"

    def submit(self):
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save()
            self.opportunity.increment_applications()


class SavedOpportunity(models.Model):
    """User saved/bookmarked opportunities"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='saved_by_users')
    notes = models.TextField(blank=True, help_text="Personal notes about this opportunity")
    reminder_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'opportunity']

    def __str__(self):
        return f"{self.user.get_display_name()} saved {self.opportunity.title}"


class OpportunityAlert(models.Model):
    """Email alerts for new opportunities matching criteria"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='opportunity_alerts')
    name = models.CharField(max_length=100)

    # Alert criteria
    opportunity_types = models.JSONField(default=list, help_text="List of opportunity types")
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords")
    location = models.CharField(max_length=200, blank=True)
    is_remote_only = models.BooleanField(default=False)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Alert settings
    is_active = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=[
        ('instant', 'Instant'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='weekly')
    last_sent = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.get_display_name()}"