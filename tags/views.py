from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db.models import Q, Count, F
from django.contrib.contenttypes.models import ContentType
from .models import Category, Tag, SubTag, UserSubscription, PushSubscription, UserInterest
from .serializers import (
    CategorySerializer, TagSerializer, SubTagSerializer,
    UserSubscriptionSerializer, PushSubscriptionSerializer,
    UserInterestSerializer, SubscriptionStatsSerializer
)
from .push_notifications import send_push_notification


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Annotate with counts
        queryset = queryset.annotate(
            tag_count=Count('tags'),
            subscriber_count=Count('subscribers')
        )
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, slug=None):
        """Subscribe to a category"""
        category = self.get_object()

        # Check if already subscribed
        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            category=category,
            defaults={
                'push_notifications': request.data.get('push_notifications', True),
                'email_notifications': request.data.get('email_notifications', True),
                'notification_frequency': request.data.get('notification_frequency', 'instant')
            }
        )

        if not created:
            return Response({
                'message': 'Already subscribed to this category',
                'subscription': UserSubscriptionSerializer(subscription).data
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Successfully subscribed to category',
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unsubscribe(self, request, slug=None):
        """Unsubscribe from a category"""
        category = self.get_object()

        deleted_count = UserSubscription.objects.filter(
            user=request.user,
            category=category
        ).delete()[0]

        if deleted_count:
            return Response({
                'message': 'Successfully unsubscribed from category'
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Not subscribed to this category'
        }, status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tags"""
    queryset = Tag.objects.filter(is_active=True)
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category if provided
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Sort by popularity or alphabetically
        sort_by = self.request.query_params.get('sort', 'popular')
        if sort_by == 'popular':
            queryset = queryset.order_by('-usage_count', 'name')
        else:
            queryset = queryset.order_by('name')

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, slug=None):
        """Subscribe to a tag"""
        tag = self.get_object()

        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            tag=tag,
            defaults={
                'push_notifications': request.data.get('push_notifications', True),
                'email_notifications': request.data.get('email_notifications', True),
                'notification_frequency': request.data.get('notification_frequency', 'instant')
            }
        )

        if not created:
            return Response({
                'message': 'Already subscribed to this tag',
                'subscription': UserSubscriptionSerializer(subscription).data
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Successfully subscribed to tag',
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unsubscribe(self, request, slug=None):
        """Unsubscribe from a tag"""
        tag = self.get_object()

        deleted_count = UserSubscription.objects.filter(
            user=request.user,
            tag=tag
        ).delete()[0]

        if deleted_count:
            return Response({
                'message': 'Successfully unsubscribed from tag'
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Not subscribed to this tag'
        }, status=status.HTTP_404_NOT_FOUND)


class SubTagViewSet(viewsets.ModelViewSet):
    """ViewSet for SubTags"""
    queryset = SubTag.objects.filter(is_active=True)
    serializer_class = SubTagSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by parent tag if provided
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(parent_tag__slug=tag_slug)

        return queryset


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for User Subscriptions"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscription statistics for current user"""
        subscriptions = self.get_queryset()

        stats = {
            'total_subscriptions': subscriptions.count(),
            'category_subscriptions': subscriptions.filter(category__isnull=False).count(),
            'tag_subscriptions': subscriptions.filter(tag__isnull=False).count(),
            'subtag_subscriptions': subscriptions.filter(subtag__isnull=False).count(),
            'push_enabled_count': subscriptions.filter(push_notifications=True).count(),
            'email_enabled_count': subscriptions.filter(email_notifications=True).count(),
        }

        serializer = SubscriptionStatsSerializer(stats)
        return Response(serializer.data)


class PushSubscriptionView(APIView):
    """Manage push notification subscriptions"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create or update push subscription"""
        serializer = PushSubscriptionSerializer(data=request.data)

        if serializer.is_valid():
            # Check if subscription already exists
            endpoint = serializer.validated_data['endpoint']
            subscription, created = PushSubscription.objects.update_or_create(
                endpoint=endpoint,
                defaults={
                    'user': request.user,
                    'p256dh': serializer.validated_data['p256dh'],
                    'auth': serializer.validated_data['auth'],
                    'device_name': serializer.validated_data.get('device_name', ''),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'is_active': True
                }
            )

            return Response({
                'message': 'Push subscription saved successfully',
                'subscription': PushSubscriptionSerializer(subscription).data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete push subscription"""
        endpoint = request.data.get('endpoint')

        if not endpoint:
            return Response({
                'error': 'Endpoint is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint
        ).delete()[0]

        if deleted_count:
            return Response({
                'message': 'Push subscription removed successfully'
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Push subscription not found'
        }, status=status.HTTP_404_NOT_FOUND)


class RecommendedFeedView(APIView):
    """Get personalized content feed based on user interests (Twitter-like algorithm)"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Get personalized feed"""
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))

        if request.user.is_authenticated:
            # Personalized feed for authenticated users
            feed = self._get_personalized_feed(request.user, page_size, page)
        else:
            # Trending feed for anonymous users
            feed = self._get_trending_feed(page_size, page)

        return Response(feed)

    def _get_personalized_feed(self, user, page_size, page):
        """Generate personalized feed based on user interests and subscriptions"""
        from news.models import Article
        from events.models import Event
        from opportunities.models import Opportunity

        # Get user interests
        interests = UserInterest.objects.filter(user=user).order_by('-score')[:10]
        subscriptions = UserSubscription.objects.filter(user=user)

        # Build query for content based on interests and subscriptions
        content_ids = []

        # Get content from subscribed categories and tags
        for subscription in subscriptions:
            # This is simplified - you'd need to add tag fields to your models
            # and implement proper filtering
            pass

        # Get recent articles with scoring
        articles = Article.objects.filter(
            status='published'
        ).select_related('category').prefetch_related('tags')[:page_size * 3]

        # Score articles based on user interests
        scored_content = []
        for article in articles:
            score = self._calculate_content_score(article, interests, subscriptions)
            scored_content.append({
                'type': 'article',
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt,
                'image': article.image.url if article.image else None,
                'published_at': article.published_at,
                'score': score,
                'category': article.category.name if hasattr(article, 'category') else None,
            })

        # Sort by score
        scored_content.sort(key=lambda x: x['score'], reverse=True)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size

        return {
            'feed': scored_content[start:end],
            'page': page,
            'page_size': page_size,
            'total': len(scored_content),
            'algorithm': 'personalized'
        }

    def _get_trending_feed(self, page_size, page):
        """Get trending content for non-authenticated users"""
        from news.models import Article

        # Get trending articles (most viewed/liked in last 7 days)
        from django.utils import timezone
        from datetime import timedelta

        week_ago = timezone.now() - timedelta(days=7)

        articles = Article.objects.filter(
            status='published',
            published_at__gte=week_ago
        ).order_by('-view_count', '-published_at')[:page_size * 2]

        content = []
        for article in articles:
            content.append({
                'type': 'article',
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt if hasattr(article, 'excerpt') else '',
                'image': article.image.url if article.image else None,
                'published_at': article.published_at,
                'view_count': article.view_count,
                'category': article.category.name if hasattr(article, 'category') else None,
            })

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size

        return {
            'feed': content[start:end],
            'page': page,
            'page_size': page_size,
            'total': len(content),
            'algorithm': 'trending'
        }

    def _calculate_content_score(self, content, interests, subscriptions):
        """Calculate relevance score for content based on user interests"""
        score = 0.0

        # Base score from recency (newer content gets higher score)
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        if hasattr(content, 'published_at') and content.published_at:
            age_hours = (now - content.published_at).total_seconds() / 3600
            recency_score = max(0, 100 - (age_hours / 24 * 10))  # Decay over days
            score += recency_score

        # Score from user interests
        # You'd need to implement tag relationships in your content models

        # Score from engagement
        if hasattr(content, 'view_count'):
            score += content.view_count * 0.1

        # Boost subscribed content
        # Check if content matches user subscriptions
        # This needs proper implementation based on your models

        return score


class TrackInteractionView(APIView):
    """Track user interactions for algorithm training"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Track an interaction"""
        interaction_type = request.data.get('type')  # view, like, share
        category_id = request.data.get('category_id')
        tag_id = request.data.get('tag_id')
        time_spent = request.data.get('time_spent', 0)

        if not interaction_type:
            return Response({
                'error': 'Interaction type is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Track category interest
        if category_id:
            interest, created = UserInterest.objects.get_or_create(
                user=request.user,
                category_id=category_id
            )

            if interaction_type == 'view':
                interest.view_count += 1
            elif interaction_type == 'like':
                interest.like_count += 1
            elif interaction_type == 'share':
                interest.share_count += 1

            if time_spent:
                interest.time_spent += time_spent

            interest.calculate_score()

        # Track tag interest
        if tag_id:
            interest, created = UserInterest.objects.get_or_create(
                user=request.user,
                tag_id=tag_id
            )

            if interaction_type == 'view':
                interest.view_count += 1
            elif interaction_type == 'like':
                interest.like_count += 1
            elif interaction_type == 'share':
                interest.share_count += 1

            if time_spent:
                interest.time_spent += time_spent

            interest.calculate_score()

        return Response({
            'message': 'Interaction tracked successfully'
        }, status=status.HTTP_200_OK)
