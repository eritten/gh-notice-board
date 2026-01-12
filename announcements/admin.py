from django.contrib import admin
from .models import Announcement, AnnouncementImage, AnnouncementAcknowledgment, AnnouncementTranslation, AnnouncementAlert


class AnnouncementImageInline(admin.TabularInline):
    model = AnnouncementImage
    extra = 1


class AnnouncementTranslationInline(admin.TabularInline):
    model = AnnouncementTranslation
    extra = 1


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'source_organization', 'priority', 'is_emergency',
                    'is_national', 'status', 'expires_at', 'views_count', 'published_at']
    list_filter = ['status', 'priority', 'is_emergency', 'is_national',
                   'announcement_type', 'target_audience', 'published_at']
    search_fields = ['title', 'content', 'source_organization']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    inlines = [AnnouncementImageInline, AnnouncementTranslationInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'summary', 'content', 'announcement_type', 'category')
        }),
        ('Source & Contact', {
            'fields': ('posted_by', 'source_organization', 'organization_logo', 'organization_verified',
                       'contact_person', 'contact_email', 'contact_phone', 'website_url')
        }),
        ('Location', {
            'fields': ('is_national', 'regions', 'districts', 'location_details')
        }),
        ('Media', {
            'fields': ('featured_image', 'document', 'document_title', 'video_url')
        }),
        ('Priority & Status', {
            'fields': ('priority', 'status', 'is_emergency', 'is_pinned', 'is_featured',
                       'publish_at', 'expires_at', 'published_at')
        }),
        ('Actions', {
            'fields': ('action_required', 'action_deadline', 'action_url', 'action_instructions'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'shares_count', 'acknowledgments_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnnouncementAcknowledgment)
class AnnouncementAcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'announcement', 'acknowledged_at']
    list_filter = ['acknowledged_at']
    search_fields = ['user__username', 'announcement__title']


@admin.register(AnnouncementAlert)
class AnnouncementAlertAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'alert_type',
                    'recipient_count', 'is_sent', 'sent_at']
    list_filter = ['alert_type', 'is_sent', 'sent_at']
    search_fields = ['announcement__title']
