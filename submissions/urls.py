from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentSubmissionViewSet, ContactMessageViewSet

router = DefaultRouter()
router.register(r'submissions/content', ContentSubmissionViewSet, basename='content-submission')
router.register(r'submissions/contact', ContactMessageViewSet, basename='contact-message')

urlpatterns = router.urls
