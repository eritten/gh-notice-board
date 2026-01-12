from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet, RegisterView, CustomTokenObtainPairView,
    LogoutView, VerifyEmailView
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

app_name = 'authentication'

urlpatterns = [
    # JWT Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),

    # Include router URLs
    path('', include(router.urls)),
]