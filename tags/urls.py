from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    TagViewSet,
    SubTagViewSet,
    UserSubscriptionViewSet,
    PushSubscriptionView,
    RecommendedFeedView,
    TrackInteractionView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'subtags', SubTagViewSet, basename='subtag')
router.register(r'subscriptions', UserSubscriptionViewSet, basename='subscription')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Push notifications
    path('push/subscribe/', PushSubscriptionView.as_view(), name='push-subscribe'),

    # Personalized feed
    path('feed/recommended/', RecommendedFeedView.as_view(), name='recommended-feed'),

    # Track interactions
    path('track/interaction/', TrackInteractionView.as_view(), name='track-interaction'),
]
