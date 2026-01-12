from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import NewsletterSubscriber, Newsletter
from .serializers import (
    NewsletterSubscriberListSerializer, NewsletterSubscriberDetailSerializer,
    NewsletterSubscriberCreateSerializer, NewsletterListSerializer,
    NewsletterDetailSerializer
)


class NewsletterSubscriberViewSet(viewsets.ModelViewSet):
    queryset = NewsletterSubscriber.objects.all()
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'subscribe_news', 'subscribe_events',
                        'subscribe_opportunities', 'subscribe_diaspora']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return NewsletterSubscriberCreateSerializer
        elif self.action == 'retrieve':
            return NewsletterSubscriberDetailSerializer
        return NewsletterSubscriberListSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return NewsletterSubscriber.objects.all()
        if self.action == 'create':
            return NewsletterSubscriber.objects.all()
        return NewsletterSubscriber.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'Successfully subscribed to newsletter!'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe from newsletter"""
        subscriber = self.get_object()
        subscriber.status = 'unsubscribed'
        subscriber.save()
        return Response({'message': 'Successfully unsubscribed'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active subscribers"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        subscribers = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(subscribers, many=True)
        return Response(serializer.data)


class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'newsletter_type']
    search_fields = ['title', 'subject', 'content_html']
    ordering_fields = ['created_at', 'scheduled_for', 'sent_at']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NewsletterDetailSerializer
        return NewsletterListSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Newsletter.objects.all()
        return Newsletter.objects.none()

    @action(detail=False, methods=['get'])
    def drafts(self, request):
        """Get draft newsletters"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        newsletters = self.get_queryset().filter(status='draft')
        serializer = self.get_serializer(newsletters, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def scheduled(self, request):
        """Get scheduled newsletters"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        newsletters = self.get_queryset().filter(status='scheduled')
        serializer = self.get_serializer(newsletters, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get sent newsletters"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        newsletters = self.get_queryset().filter(status='sent')
        serializer = self.get_serializer(newsletters, many=True)
        return Response(serializer.data)
