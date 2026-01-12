from django.contrib import admin
from .models import ContentSubmission, ContactMessage


@admin.register(ContentSubmission)
class ContentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['title', 'submission_type', 'submitter_name', 'submitter_email',
                    'status', 'created_at', 'reviewed_at']
    list_filter = ['submission_type', 'status', 'created_at']
    search_fields = ['title', 'content', 'submitter_name', 'submitter_email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_submissions', 'reject_submissions']
    fieldsets = (
        ('Submission Details', {
            'fields': ('submission_type', 'title', 'content', 'additional_data')
        }),
        ('Submitter Information', {
            'fields': ('submitter_name', 'submitter_email', 'submitter_phone')
        }),
        ('Media', {
            'fields': ('image', 'document')
        }),
        ('Review', {
            'fields': ('status', 'admin_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_submissions(self, request, queryset):
        queryset.update(status='approved')
    approve_submissions.short_description = "Approve selected submissions"

    def reject_submissions(self, request, queryset):
        queryset.update(status='rejected')
    reject_submissions.short_description = "Reject selected submissions"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'is_read', 'is_responded', 'created_at']
    list_filter = ['is_read', 'is_responded', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_responded']
    fieldsets = (
        ('Contact Details', {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_responded', 'admin_notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark as read"

    def mark_as_responded(self, request, queryset):
        queryset.update(is_responded=True)
    mark_as_responded.short_description = "Mark as responded"
