from django.contrib import admin
from .models import NewsletterSubscriber, Newsletter, NewsletterEmail, NewsletterTemplate


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'status', 'subscribe_news',
                    'subscribe_events', 'subscribe_opportunities', 'subscribe_diaspora',
                    'created_at']
    list_filter = ['status', 'subscribe_news', 'subscribe_events',
                   'subscribe_opportunities', 'subscribe_diaspora', 'frequency']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at',
                       'confirmed_at', 'emails_sent', 'emails_opened']
    date_hierarchy = 'created_at'
    actions = ['activate_subscribers', 'deactivate_subscribers']

    fieldsets = (
        ('Contact Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'location')
        }),
        ('Subscription Preferences', {
            'fields': ('subscribe_news', 'subscribe_events', 'subscribe_opportunities',
                       'subscribe_announcements', 'subscribe_diaspora', 'subscribe_special', 'frequency')
        }),
        ('Status', {
            'fields': ('status', 'confirmed_at')
        }),
        ('Engagement', {
            'fields': ('emails_sent', 'emails_opened', 'links_clicked'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def activate_subscribers(self, request, queryset):
        queryset.update(status='active')
    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        queryset.update(status='unsubscribed')
    deactivate_subscribers.short_description = "Deactivate selected subscribers"


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'status', 'newsletter_type', 'recipients_count',
                    'sent_count', 'scheduled_for', 'sent_at', 'created_at']
    list_filter = ['status', 'newsletter_type', 'send_to_news', 'send_to_events',
                   'send_to_opportunities', 'send_to_diaspora', 'created_at']
    search_fields = ['title', 'subject', 'content_html']
    readonly_fields = ['recipients_count', 'sent_count', 'delivered_count', 'opened_count',
                       'clicked_count', 'created_at', 'sent_at']
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Newsletter Details', {
            'fields': ('title', 'slug', 'newsletter_type', 'subject', 'preheader')
        }),
        ('Content', {
            'fields': ('content_html', 'content_text')
        }),
        ('Targeting', {
            'fields': ('send_to_all', 'send_to_news', 'send_to_events',
                       'send_to_opportunities', 'send_to_announcements', 'send_to_diaspora')
        }),
        ('Sender', {
            'fields': ('from_name', 'from_email', 'reply_to_email')
        }),
        ('Status & Scheduling', {
            'fields': ('status', 'scheduled_for')
        }),
        ('Metrics', {
            'fields': ('recipients_count', 'sent_count', 'delivered_count',
                       'opened_count', 'clicked_count', 'sent_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NewsletterTemplate)
class NewsletterTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type',
                    'is_active', 'is_default', 'created_at']
    list_filter = ['template_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
