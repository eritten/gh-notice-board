from django.contrib import admin
from .models import Category, Tag, SubTag, UserSubscription, PushSubscription, UserInterest


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'tag_count', 'subscriber_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    def tag_count(self, obj):
        return obj.tags.count()
    tag_count.short_description = 'Tags'

    def subscriber_count(self, obj):
        return obj.subscribers.count()
    subscriber_count.short_description = 'Subscribers'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'usage_count', 'is_active', 'subtag_count', 'subscriber_count', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-usage_count', 'name']

    def subtag_count(self, obj):
        return obj.subtags.count()
    subtag_count.short_description = 'SubTags'

    def subscriber_count(self, obj):
        return obj.subscribers.count()
    subscriber_count.short_description = 'Subscribers'


@admin.register(SubTag)
class SubTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent_tag', 'usage_count', 'is_active', 'subscriber_count', 'created_at']
    list_filter = ['is_active', 'parent_tag', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-usage_count', 'name']

    def subscriber_count(self, obj):
        return obj.subscribers.count()
    subscriber_count.short_description = 'Subscribers'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_target', 'push_notifications',
                    'email_notifications', 'notification_frequency', 'created_at']
    list_filter = ['push_notifications', 'email_notifications', 'notification_frequency', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-created_at']

    def subscription_target(self, obj):
        if obj.category:
            return f"Category: {obj.category.name}"
        elif obj.tag:
            return f"Tag: {obj.tag.name}"
        elif obj.subtag:
            return f"SubTag: {obj.subtag.name}"
        return "No target"
    subscription_target.short_description = 'Subscribed To'


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'device_name']
    readonly_fields = ['endpoint', 'p256dh', 'auth', 'user_agent']
    ordering = ['-created_at']


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ['user', 'interest_target', 'score', 'view_count',
                    'like_count', 'share_count', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username']
    ordering = ['-score']
    readonly_fields = ['score']

    def interest_target(self, obj):
        if obj.category:
            return f"Category: {obj.category.name}"
        elif obj.tag:
            return f"Tag: {obj.tag.name}"
        return "No target"
    interest_target.short_description = 'Interest In'
