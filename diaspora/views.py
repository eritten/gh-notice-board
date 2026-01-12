from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import DiasporaPost, DiasporaNetwork, DiasporaDirectory, DiasporaInvestment
from .serializers import (
    DiasporaPostListSerializer, DiasporaPostDetailSerializer
)


class DiasporaPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DiasporaPost.objects.filter(
        status='published').select_related('category', 'author')
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['content_type', 'category__slug',
                        'country', 'region', 'is_featured', 'is_urgent']
    search_fields = ['title', 'content', 'country', 'organization_name']
    ordering_fields = ['published_at', 'views_count', 'created_at']
    ordering = ['-published_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DiasporaPostDetailSerializer
        return DiasporaPostListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        posts = self.get_queryset().filter(is_featured=True)[:5]
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get urgent diaspora posts"""
        posts = self.get_queryset().filter(is_urgent=True)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def embassy(self, request):
        """Get embassy notices"""
        posts = self.get_queryset().filter(content_type='embassy')
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def immigration(self, request):
        """Get immigration updates"""
        posts = self.get_queryset().filter(content_type='immigration')
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_country(self, request):
        """Get posts by country"""
        country = request.query_params.get('country')
        if country:
            posts = self.get_queryset().filter(country__icontains=country)
            serializer = self.get_serializer(posts, many=True)
            return Response(serializer.data)
        return Response({'error': 'Country parameter required'}, status=status.HTTP_400_BAD_REQUEST)
