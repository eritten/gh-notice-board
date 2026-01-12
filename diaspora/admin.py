from django.contrib import admin
from .models import DiasporaPost, DiasporaImage, DiasporaNetwork, DiasporaDirectory, DiasporaInvestment


class DiasporaImageInline(admin.TabularInline):
    model = DiasporaImage
    extra = 1


@admin.register(DiasporaPost)
class DiasporaPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'country', 'region', 'status',
                    'is_featured', 'is_urgent', 'views_count', 'published_at']
    list_filter = ['status', 'content_type', 'is_featured', 'is_urgent',
                   'region', 'category', 'published_at']
    search_fields = ['title', 'content', 'country', 'organization_name']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    inlines = [DiasporaImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'summary', 'content', 'content_type', 'category')
        }),
        ('Location', {
            'fields': ('region', 'country', 'city', 'diaspora_community')
        }),
        ('Organization', {
            'fields': ('organization_name', 'organization_type', 'organization_logo', 'organization_verified')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_video_url')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email', 'contact_phone', 'whatsapp_number', 'website_url'),
            'classes': ('collapse',)
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'is_trending', 'is_urgent', 'is_pinned', 'published_at')
        }),
        ('Statistics', {
            'fields': ('views_count', 'likes_count', 'comments_count', 'shares_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DiasporaNetwork)
class DiasporaNetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'network_type', 'based_in_country',
                    'membership_count', 'is_verified', 'is_active']
    list_filter = ['network_type', 'is_verified',
                   'is_active', 'based_in_country']
    search_fields = ['name', 'description',
                     'based_in_country', 'based_in_city']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DiasporaDirectory)
class DiasporaDirectoryAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'listing_type', 'profession',
                    'current_country', 'is_verified', 'is_active']
    list_filter = ['listing_type', 'profession',
                   'is_verified', 'is_active', 'current_country']
    search_fields = ['full_name', 'business_name',
                     'professional_title', 'current_country']


@admin.register(DiasporaInvestment)
class DiasporaInvestmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'investment_type', 'investment_stage',
                    'minimum_investment', 'is_verified', 'is_active']
    list_filter = ['investment_type',
                   'investment_stage', 'is_verified', 'is_active']
    search_fields = ['title', 'company_name', 'description']
    prepopulated_fields = {'slug': ('title',)}
