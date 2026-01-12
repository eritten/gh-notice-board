from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters import rest_framework as filters
from django.db.models import Q, Count, F, Prefetch
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from .models import NewsArticle, NewsImage, NewsRevision
from .serializers import (
    NewsArticleListSerializer, NewsArticleDetailSerializer,
    NewsArticleCreateUpdateSerializer, NewsRevisionSerializer
)
from interactions.models import Like, Bookmark, View, Share, Comment
from authentication.permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly


class NewsArticleFilter(filters.FilterSet):
    """Filter for news articles"""
    search = filters.CharFilter(method='filter_search')
    category = filters.UUIDFilter(field_name='category__id')
    category_slug = filters.CharFilter(field_name='category__slug')
    tag = filters.CharFilter(field_name='tags__slug')
    author = filters.UUIDFilter(field_name='author__id')
    status = filters.ChoiceFilter(choices=NewsArticle.STATUS_CHOICES)
    is_featured = filters.BooleanFilter()
    is_breaking = filters.BooleanFilter()
    is_trending = filters.BooleanFilter()
    is_ai_generated = filters.BooleanFilter()
    date_from = filters.DateFilter(
        field_name='published_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='published_at', lookup_expr='lte')

    class Meta:
        model = NewsArticle
        fields = [
            'search', 'category', 'category_slug', 'tag', 'author', 'status',
            'is_featured', 'is_breaking', 'is_trending', 'is_ai_generated',
            'date_from', 'date_to'
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(summary__icontains=value) |
            Q(author__username__icontains=value) |
            Q(author__first_name__icontains=value) |
            Q(author__last_name__icontains=value)
        )


class NewsArticleViewSet(viewsets.ModelViewSet):
    """ViewSet for news articles with full CRUD and engagement features"""
    queryset = NewsArticle.objects.select_related('author', 'category', 'published_by').prefetch_related(
        'tags', 'gallery_images'
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = NewsArticleFilter
    search_fields = ['title', 'content', 'summary', 'author__username']
    ordering_fields = [
        'published_at', 'created_at', 'views_count', 'likes_count',
        'comments_count', 'shares_count'
    ]
    ordering = ['-published_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return NewsArticleCreateUpdateSerializer
        elif self.action == 'retrieve':
            return NewsArticleDetailSerializer
        return NewsArticleListSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action in ['publish', 'unpublish']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Get article details and track view"""
        instance = self.get_object()
        if request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(NewsArticle)
            View.objects.get_or_create(
                user=request.user,
                content_type=content_type,
                object_id=instance.id
            )
            instance.views_count = F('views_count') + 1
            instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        """Like or unlike an article"""
        article = self.get_object()
        content_type = ContentType.objects.get_for_model(NewsArticle)
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=article.id
        )
        if not created:
            like.delete()
            article.likes_count = F('likes_count') - 1
            article.save(update_fields=['likes_count'])
            return Response({'liked': False, 'likes_count': article.likes_count})
        article.likes_count = F('likes_count') + 1
        article.save(update_fields=['likes_count'])
        return Response({'liked': True, 'likes_count': article.likes_count})

    @action(detail=True, methods=['post'])
    def bookmark(self, request, slug=None):
        """Bookmark or unbookmark an article"""
        article = self.get_object()
        content_type = ContentType.objects.get_for_model(NewsArticle)
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=article.id
        )
        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})
        return Response({'bookmarked': True})

    @action(detail=True, methods=['post'])
    def share(self, request, slug=None):
        """Share an article"""
        article = self.get_object()
        content_type = ContentType.objects.get_for_model(NewsArticle)
        platform = request.data.get('platform', 'internal')
        Share.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=article.id,
            platform=platform
        )
        article.shares_count = F('shares_count') + 1
        article.save(update_fields=['shares_count'])
        return Response({'shared': True, 'shares_count': article.shares_count})

    @action(detail=True, methods=['get'])
    def comments(self, request, slug=None):
        """Get article comments"""
        article = self.get_object()
        content_type = ContentType.objects.get_for_model(NewsArticle)
        comments = Comment.objects.filter(
            content_type=content_type,
            object_id=article.id,
            parent__isnull=True
        ).select_related('user').prefetch_related('replies')
        page = self.paginate_queryset(comments)
        if page is not None:
            from interactions.serializers import CommentSerializer
            serializer = CommentSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        from interactions.serializers import CommentSerializer
        serializer = CommentSerializer(
            comments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending articles based on engagement"""
        seven_days_ago = timezone.now() - timedelta(days=7)
        articles = self.get_queryset().filter(
            published_at__gte=seven_days_ago
        ).annotate(
            engagement_score=(
                F('views_count') * 1 +
                F('likes_count') * 5 +
                F('comments_count') * 10 +
                F('shares_count') * 15
            )
        ).order_by('-engagement_score')[:20]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def breaking(self, request):
        """Get breaking news"""
        articles = self.get_queryset().filter(is_breaking=True)[:5]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured articles"""
        articles = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish(self, request, slug=None):
        """Publish a draft article"""
        article = self.get_object()
        if article.status == 'published':
            return Response({'detail': 'Article is already published'}, status=status.HTTP_400_BAD_REQUEST)
        article.status = 'published'
        article.published_at = timezone.now()
        article.published_by = request.user
        article.save()
        serializer = self.get_serializer(article)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def revisions(self, request, slug=None):
        """Get article revision history"""
        article = self.get_object()
        revisions = article.revisions.all()
        serializer = NewsRevisionSerializer(revisions, many=True)
        return Response(serializer.data)


class NewsRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing article revisions"""
    queryset = NewsRevision.objects.select_related('article', 'revision_by')
    serializer_class = NewsRevisionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(
            Q(article__author=self.request.user) |
            Q(article__status='published')
        )
