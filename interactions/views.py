from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from .models import Like, Dislike, Review, Bookmark
from .serializers import (
    LikeSerializer, DislikeSerializer, ReviewSerializer,
    BookmarkSerializer, BookmarkCreateSerializer, BookmarkDeleteSerializer,
    InteractionStatsSerializer, BOOKMARK_TYPE_MODEL_MAP, normalize_bookmark_type
)


class LikeToggleView(APIView):
    """Toggle like for any content"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content_type_id = request.data.get('content_type')
        object_id = request.data.get('object_id')

        if not content_type_id or not object_id:
            return Response({
                'error': 'content_type and object_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type = ContentType.objects.get(id=content_type_id)
        except ContentType.DoesNotExist:
            return Response({
                'error': 'Invalid content_type'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if already liked
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        )

        if not created:
            # Unlike
            like.delete()
            return Response({
                'message': 'Unliked',
                'liked': False
            }, status=status.HTTP_200_OK)

        # Remove dislike if exists
        Dislike.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).delete()

        return Response({
            'message': 'Liked',
            'liked': True,
            'like': LikeSerializer(like).data
        }, status=status.HTTP_201_CREATED)


class DislikeToggleView(APIView):
    """Toggle dislike for any content"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content_type_id = request.data.get('content_type')
        object_id = request.data.get('object_id')

        if not content_type_id or not object_id:
            return Response({
                'error': 'content_type and object_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type = ContentType.objects.get(id=content_type_id)
        except ContentType.DoesNotExist:
            return Response({
                'error': 'Invalid content_type'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if already disliked
        dislike, created = Dislike.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        )

        if not created:
            # Remove dislike
            dislike.delete()
            return Response({
                'message': 'Dislike removed',
                'disliked': False
            }, status=status.HTTP_200_OK)

        # Remove like if exists
        Like.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).delete()

        return Response({
            'message': 'Disliked',
            'disliked': True,
            'dislike': DislikeSerializer(dislike).data
        }, status=status.HTTP_201_CREATED)


class ReviewListCreateView(generics.ListCreateAPIView):
    """List and create reviews for content"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        content_type_id = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')

        if content_type_id and object_id:
            return Review.objects.filter(
                content_type_id=content_type_id,
                object_id=object_id,
                is_approved=True
            )

        return Review.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a review"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class BookmarkToggleView(APIView):
    """Toggle bookmark for any content"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content_type_id = request.data.get('content_type')
        object_id = request.data.get('object_id')

        if not content_type_id or not object_id:
            return Response({
                'error': 'content_type and object_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type = ContentType.objects.get(id=content_type_id)
        except ContentType.DoesNotExist:
            return Response({
                'error': 'Invalid content_type'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if already bookmarked
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        )

        if not created:
            # Remove bookmark
            bookmark.delete()
            return Response({
                'message': 'Bookmark removed',
                'bookmarked': False
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Bookmarked',
            'bookmarked': True,
            'bookmark': BookmarkSerializer(bookmark).data
        }, status=status.HTTP_201_CREATED)


class UserBookmarksView(generics.ListAPIView):
    """List user's bookmarks"""
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class BookmarkView(APIView):
    """Create, list, and delete bookmarks across supported content types."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Bookmark.objects.filter(user=request.user)

        bookmark_type = request.query_params.get('type')
        if bookmark_type:
            normalized_type = normalize_bookmark_type(bookmark_type)
            if not normalized_type:
                allowed_types = ', '.join(sorted(BOOKMARK_TYPE_MODEL_MAP.keys()))
                return Response({
                    'error': f"Unsupported type '{bookmark_type}'. Use one of: {allowed_types}."
                }, status=status.HTTP_400_BAD_REQUEST)
            content_type = ContentType.objects.get_for_model(BOOKMARK_TYPE_MODEL_MAP[normalized_type])
            queryset = queryset.filter(content_type=content_type)

        serializer = BookmarkSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            content_type=serializer.validated_data['content_type'],
            object_id=serializer.validated_data['object_id']
        )

        response_data = {
            'message': 'Bookmarked' if created else 'Already bookmarked',
            'bookmarked': True,
            'bookmark': BookmarkSerializer(bookmark, context={'request': request}).data
        }
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_data, status=response_status)

    def delete(self, request):
        serializer = BookmarkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deleted_count, _ = Bookmark.objects.filter(
            user=request.user,
            content_type=serializer.validated_data['content_type'],
            object_id=serializer.validated_data['object_id']
        ).delete()

        if deleted_count == 0:
            return Response({
                'message': 'Bookmark was not found',
                'bookmarked': False
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Bookmark removed',
            'bookmarked': False
        }, status=status.HTTP_200_OK)


class InteractionStatsView(APIView):
    """Get interaction statistics for content"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        content_type_id = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')

        if not content_type_id or not object_id:
            return Response({
                'error': 'content_type and object_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type = ContentType.objects.get(id=content_type_id)
        except ContentType.DoesNotExist:
            return Response({
                'error': 'Invalid content_type'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get stats
        likes_count = Like.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).count()

        dislikes_count = Dislike.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).count()

        reviews = Review.objects.filter(
            content_type=content_type,
            object_id=object_id,
            is_approved=True
        )

        reviews_count = reviews.count()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # User-specific data
        user_liked = False
        user_disliked = False
        user_bookmarked = False
        user_review = None

        if request.user.is_authenticated:
            user_liked = Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=object_id
            ).exists()

            user_disliked = Dislike.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=object_id
            ).exists()

            user_bookmarked = Bookmark.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=object_id
            ).exists()

            try:
                user_review = Review.objects.get(
                    user=request.user,
                    content_type=content_type,
                    object_id=object_id
                )
            except Review.DoesNotExist:
                pass

        data = {
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'reviews_count': reviews_count,
            'average_rating': round(average_rating, 2),
            'user_liked': user_liked,
            'user_disliked': user_disliked,
            'user_bookmarked': user_bookmarked,
            'user_review': ReviewSerializer(user_review).data if user_review else None
        }

        serializer = InteractionStatsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
