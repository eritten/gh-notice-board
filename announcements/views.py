from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from .models import Announcement, AnnouncementAcknowledgment
from .serializers import (
    AnnouncementListSerializer, AnnouncementDetailSerializer
)


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Announcement.objects.filter(
        status='published').select_related('category', 'posted_by')
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['announcement_type', 'priority',
                        'is_emergency', 'is_national', 'target_audience']
    search_fields = ['title', 'content', 'source_organization']
    ordering_fields = ['published_at', 'priority', 'views_count', 'created_at']
    ordering = ['-priority', '-published_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AnnouncementDetailSerializer
        return AnnouncementListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Exclude expired announcements
        now = timezone.now()
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=now)
        )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def emergency(self, request):
        """Get emergency announcements"""
        announcements = self.get_queryset().filter(is_emergency=True)
        serializer = self.get_serializer(announcements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get urgent priority announcements"""
        announcements = self.get_queryset().filter(priority='urgent')
        serializer = self.get_serializer(announcements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def national(self, request):
        """Get national announcements"""
        announcements = self.get_queryset().filter(is_national=True)
        serializer = self.get_serializer(announcements, many=True)
        return Response(serializer.data)
