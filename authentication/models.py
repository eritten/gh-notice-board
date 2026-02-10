from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
import uuid


def user_avatar_path(instance, filename):
    """Generate path for user avatar uploads"""
    ext = filename.split('.')[-1]
    return f'avatars/{instance.id}/{uuid.uuid4()}.{ext}'


def user_cover_path(instance, filename):
    """Generate path for user cover image uploads"""
    ext = filename.split('.')[-1]
    return f'covers/{instance.id}/{uuid.uuid4()}.{ext}'


class User(AbstractUser):
    """Custom User model with extended features"""

    # Profile Information
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    website = models.URLField(_('website'), blank=True)

    # Social Media Links
    twitter_username = models.CharField(_('Twitter username'), max_length=50, blank=True)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)
    github_username = models.CharField(_('GitHub username'), max_length=50, blank=True)

    # Profile Images
    avatar = models.ImageField(_('avatar'), upload_to=user_avatar_path, null=True, blank=True)
    cover_image = models.ImageField(_('cover image'), upload_to=user_cover_path, null=True, blank=True)

    # User Preferences
    is_public = models.BooleanField(_('public profile'), default=True)
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)

    # Twitter-like Features
    followers = models.ManyToManyField(
        'self',
        related_name='following',
        symmetrical=False,
        blank=True
    )

    # Verification
    is_verified = models.BooleanField(_('verified'), default=False)
    verification_badge = models.CharField(_('verification badge'), max_length=50, blank=True)

    # Stats
    posts_count = models.PositiveIntegerField(_('posts count'), default=0)
    followers_count = models.PositiveIntegerField(_('followers count'), default=0)
    following_count = models.PositiveIntegerField(_('following count'), default=0)

    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_seen = models.DateTimeField(_('last seen'), null=True, blank=True)

    # User Type
    USER_TYPE_CHOICES = [
        ('regular', _('Regular User')),
        ('journalist', _('Journalist')),
        ('organization', _('Organization')),
        ('government', _('Government Official')),
        ('verified', _('Verified Account')),
    ]
    user_type = models.CharField(
        _('user type'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='regular'
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return the full name of the user"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def get_display_name(self):
        """Return display name with verification badge if applicable"""
        name = self.get_full_name()
        if self.is_verified and self.verification_badge:
            return f"{name} {self.verification_badge}"
        return name

    def follow(self, user):
        """Follow another user"""
        if user != self and not self.followers.filter(pk=user.pk).exists():
            self.followers.add(user)
            self.following_count += 1
            user.followers_count += 1
            self.save(update_fields=['following_count'])
            user.save(update_fields=['followers_count'])

    def unfollow(self, user):
        """Unfollow a user"""
        if self.followers.filter(pk=user.pk).exists():
            self.followers.remove(user)
            self.following_count = max(0, self.following_count - 1)
            user.followers_count = max(0, user.followers_count - 1)
            self.save(update_fields=['following_count'])
            user.save(update_fields=['followers_count'])

    def is_following(self, user):
        """Check if following a user"""
        return self.followers.filter(pk=user.pk).exists()


class UserProfile(models.Model):
    """Extended user profile for additional metadata"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Professional Information
    occupation = models.CharField(_('occupation'), max_length=100, blank=True)
    company = models.CharField(_('company'), max_length=100, blank=True)
    skills = models.JSONField(_('skills'), default=list, blank=True)

    # Interests
    # interests = models.ManyToManyField('tags.Tag', related_name='interested_users', blank=True)

    # Privacy Settings
    show_email = models.BooleanField(_('show email'), default=False)
    show_location = models.BooleanField(_('show location'), default=True)
    allow_messages = models.BooleanField(_('allow messages'), default=True)

    # Theme Preferences
    theme = models.CharField(
        _('theme'),
        max_length=20,
        choices=[
            ('light', _('Light')),
            ('dark', _('Dark')),
            ('auto', _('Auto')),
        ],
        default='auto'
    )

    language = models.CharField(
        _('language'),
        max_length=10,
        choices=[
            ('en', _('English')),
            ('tw', _('Twi')),
            ('ga', _('Ga')),
            ('ee', _('Ewe')),
        ],
        default='en'
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.username}'s profile"
