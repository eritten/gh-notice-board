from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiasporaPostViewSet

router = DefaultRouter()
router.register(r'diaspora', DiasporaPostViewSet, basename='diaspora-post')

urlpatterns = router.urls
