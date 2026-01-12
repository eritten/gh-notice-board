from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EventCategoryViewSet, EventViewSet, EventSpeakerViewSet,
    EventSponsorViewSet, EventRegistrationViewSet
)

router = DefaultRouter()
router.register(r'categories', EventCategoryViewSet, basename='event-category')
router.register(r'events', EventViewSet, basename='event')
router.register(r'speakers', EventSpeakerViewSet, basename='event-speaker')
router.register(r'sponsors', EventSponsorViewSet, basename='event-sponsor')
router.register(r'registrations', EventRegistrationViewSet, basename='event-registration')

app_name = 'events'

urlpatterns = [
    path('', include(router.urls)),
]