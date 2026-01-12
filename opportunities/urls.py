from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet, ApplicationViewSet, SavedOpportunityViewSet

router = DefaultRouter()
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'saved-opportunities', SavedOpportunityViewSet,
                basename='saved-opportunity')

urlpatterns = router.urls
