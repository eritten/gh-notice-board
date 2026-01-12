from django.contrib import admin
from .models import NewsArticle, NewsImage


class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 1


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'is_breaking', 'is_featured',
                    'is_trending', 'views_count', 'published_at']
    list_filter = ['status', 'category', 'is_breaking', 'is_featured', 'is_trending', 'published_at']
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    inlines = [NewsImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'summary', 'content', 'category')
        }),
        ('Media', {
            'fields': ('featured_image', 'image_caption')
        }),
        ('Source', {
            'fields': ('author', 'source', 'source_url')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_breaking', 'is_featured', 'is_trending', 'published_at')
        }),
        ('Statistics', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
    )
