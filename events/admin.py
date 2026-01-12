from django.contrib import admin
from .models import Event, EventCategory, EventImage, EventSpeaker, EventSponsor, EventRegistration, EventReminder


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active']


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1


class EventSpeakerInline(admin.TabularInline):
    model = EventSpeaker
    extra = 1


class EventSponsorInline(admin.TabularInline):
    model = EventSponsor
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'venue_name', 'start_date', 'event_type',
                    'status', 'is_featured', 'views_count']
    list_filter = ['status', 'category',
                   'is_featured', 'event_type', 'start_date']
    search_fields = ['title', 'description', 'venue_name']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    inlines = [EventImageInline, EventSpeakerInline, EventSponsorInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'summary', 'description', 'category')
        }),
        ('Event Type & Timing', {
            'fields': ('event_type', 'start_date', 'end_date', 'timezone')
        }),
        ('Location', {
            'fields': ('venue_name', 'venue_address', 'venue_details', 'venue_map_url')
        }),
        ('Virtual Event', {
            'fields': ('virtual_meeting_url', 'virtual_meeting_password'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Organizer & Contact', {
            'fields': ('organizer', 'contact_email', 'contact_phone', 'website_url')
        }),
        ('Registration', {
            'fields': ('registration_required', 'registration_url', 'registration_deadline',
                       'max_attendees', 'allow_waitlist', 'registration_instructions')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'early_bird_price', 'early_bird_deadline')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'is_trending', 'is_cancelled', 'cancellation_reason')
        }),
    )


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'registration_type',
                    'status', 'attendance_status', 'created_at']
    list_filter = ['status', 'registration_type', 'attendance_status']
    search_fields = ['user__email', 'event__title', 'ticket_number']
    date_hierarchy = 'created_at'
