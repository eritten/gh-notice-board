from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsletterSubscriberViewSet, NewsletterViewSet

router = DefaultRouter()
router.register(r'newsletters/subscribers', NewsletterSubscriberViewSet, basename='newsletter-subscriber')
router.register(r'newsletters', NewsletterViewSet, basename='newsletter')

urlpatterns = router.urls
