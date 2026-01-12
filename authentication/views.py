from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q, Count, F
from django_filters import rest_framework as filters
from .models import UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer, RegisterSerializer,
    ChangePasswordSerializer, UserMinimalSerializer,
    ProfileUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly

User = get_user_model()


class UserFilter(filters.FilterSet):
    """Filter for users"""
    search = filters.CharFilter(method='filter_search')
    user_type = filters.CharFilter(field_name='profile__user_type')
    is_verified = filters.BooleanFilter()
    has_profile = filters.BooleanFilter(method='filter_has_profile')
    location = filters.CharFilter(
        field_name='profile__location', lookup_expr='icontains')
    interests = filters.CharFilter(
        field_name='profile__interests', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['search', 'user_type', 'is_verified',
                  'has_profile', 'location', 'interests']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(profile__display_name__icontains=value)
        )

    def filter_has_profile(self, queryset, name, value):
        if value:
            return queryset.exclude(profile__isnull=True)
        return queryset.filter(profile__isnull=True)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model with profile management"""
    queryset = User.objects.select_related('profile')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'followers_count', 'following_count']

    def get_permissions(self):
        if self.action in ['create', 'reset_password', 'confirm_reset_password']:
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user's profile"""
        user = request.user
        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user's password"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a user"""
        user_to_follow = self.get_object()
        if user_to_follow == request.user:
            return Response(
                {'detail': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.followers.add(user_to_follow)

        # Update counts
        user_to_follow.followers_count = user_to_follow.following.count()
        user_to_follow.save()
        request.user.following_count = request.user.followers.count()
        request.user.save()

        return Response({'detail': f'You are now following {user_to_follow.username}'})

    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Unfollow a user"""
        user_to_unfollow = self.get_object()
        request.user.followers.remove(user_to_unfollow)

        # Update counts
        user_to_unfollow.followers_count = user_to_unfollow.following.count()
        user_to_unfollow.save()
        request.user.following_count = request.user.followers.count()
        request.user.save()

        return Response({'detail': f'You have unfollowed {user_to_unfollow.username}'})

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """Get user's followers"""
        user = self.get_object()
        followers = user.following.all()
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = UserMinimalSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = UserMinimalSerializer(
            followers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """Get users that this user follows"""
        user = self.get_object()
        following = user.followers.all()
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = UserMinimalSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = UserMinimalSerializer(
            following, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def suggested(self, request):
        """Get suggested users to follow"""
        # Get users the current user doesn't follow
        following_ids = request.user.followers.values_list('id', flat=True)
        suggested = User.objects.exclude(
            Q(id=request.user.id) | Q(id__in=following_ids)
        ).annotate(
            mutual_count=Count('followers', filter=Q(
                followers__in=following_ids))
        ).order_by('-mutual_count', '-followers_count')[:20]

        serializer = UserMinimalSerializer(
            suggested, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """Request password reset"""
        email = request.data.get('email')
        if not email:
            return Response(
                {'email': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Send email
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            context = {
                'user': user,
                'reset_url': reset_url
            }
            message = render_to_string(
                'auth/password_reset_email.html', context)
            send_mail(
                'Password Reset Request',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False
            )

            return Response({'detail': 'Password reset email sent'})
        except User.DoesNotExist:
            return Response({'detail': 'Password reset email sent'})

    @action(detail=False, methods=['post'])
    def confirm_reset_password(self, request):
        """Confirm password reset"""
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([uid, token, new_password]):
            return Response(
                {'detail': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Invalid or expired reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password reset successful'})


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view to include user data"""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Get user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            user = serializer.user

            # Add user data to response
            response.data['user'] = UserSerializer(
                user, context={'request': request}).data

        return response


class LogoutView(generics.GenericAPIView):
    """Logout view to blacklist token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out'})
        except Exception:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(generics.GenericAPIView):
    """Verify email address"""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response(
                {'token': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Decode token to get user
            # TODO: Implement token verification logic
            return Response({'detail': 'Email verified successfully'})
        except Exception:
            return Response(
                {'detail': 'Invalid or expired verification token'},
                status=status.HTTP_400_BAD_REQUEST
            )
