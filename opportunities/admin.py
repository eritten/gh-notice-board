from django.contrib import admin
from .models import Opportunity, OpportunityImage, Application, SavedOpportunity, OpportunityAlert


class OpportunityImageInline(admin.TabularInline):
    model = OpportunityImage
    extra = 1


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ['title', 'opportunity_type', 'organization_name', 'location',
                    'deadline', 'status', 'is_featured', 'views_count', 'applications_count',
                    'published_at']
    list_filter = ['status', 'opportunity_type', 'is_featured', 'is_remote',
                   'is_diaspora', 'published_at', 'deadline']
    search_fields = ['title', 'description', 'organization_name', 'location']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    inlines = [OpportunityImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'summary', 'description', 'opportunity_type', 'category')
        }),
        ('Organization Details', {
            'fields': ('organization_name', 'organization_logo', 'organization_website', 'contact_email', 'contact_phone')
        }),
        ('Location', {
            'fields': ('location', 'city', 'region', 'country', 'is_remote', 'is_diaspora')
        }),
        ('Job-Specific', {
            'fields': ('employment_type', 'experience_level', 'salary_min', 'salary_max', 'salary_currency', 'show_salary', 'benefits'),
            'classes': ('collapse',)
        }),
        ('Scholarship/Grant-Specific', {
            'fields': ('funding_amount', 'funding_currency', 'duration', 'eligibility_criteria', 'number_of_slots'),
            'classes': ('collapse',)
        }),
        ('Application Details', {
            'fields': ('application_method', 'application_url', 'application_email', 'application_instructions', 'deadline')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'is_trending', 'is_urgent', 'published_at')
        }),
        ('Statistics', {
            'fields': ('views_count', 'applications_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email',
                    'opportunity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'email', 'opportunity__title']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at']


@admin.register(SavedOpportunity)
class SavedOpportunityAdmin(admin.ModelAdmin):
    list_display = ['user', 'opportunity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'opportunity__title']


@admin.register(OpportunityAlert)
class OpportunityAlertAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'frequency', 'is_active', 'created_at']
    list_filter = ['frequency', 'is_active', 'created_at']
    search_fields = ['name', 'user__username']
