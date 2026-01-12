from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters import rest_framework as filters
from django.db.models import Q, Count, F, Prefetch
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from .models import Event, EventCategory, EventRegistration, EventSpeaker, EventSponsor
from .serializers import (
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    EventCategorySerializer, EventRegistrationSerializer,
    EventRegistrationCreateSerializer, EventSpeakerSerializer,
    EventSponsorSerializer
)
from interactions.models import Like, Bookmark, View, Share
from authentication.permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly


class EventCategoryFilter(filters.FilterSet):
    """Filter for event categories"""
    search = filters.CharFilter(field_name='name', lookup_expr='icontains')
    parent = filters.UUIDFilter(field_name='parent__id')
    has_parent = filters.BooleanFilter(method='filter_has_parent')

    class Meta:
        model = EventCategory
        fields = ['search', 'parent', 'has_parent', 'is_active']

    def filter_has_parent(self, queryset, name, value):
        if value:
            return queryset.exclude(parent__isnull=True)
        return queryset.filter(parent__isnull=True)


class EventCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for event categories"""
    queryset = EventCategory.objects.select_related('parent').annotate(
        events_count=Count('events')
    )
    serializer_class = EventCategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_class = EventCategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'events_count']
    ordering = ['priority', 'name']
    lookup_field = 'slug'

    @action(detail=True, methods=['get'])
    def events(self, request, slug=None):
        """Get events in this category"""
        category = self.get_object()
        events = Event.objects.filter(category=category)
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = EventListSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = EventListSerializer(
            events, many=True, context={'request': request})
        return Response(serializer.data)


class EventFilter(filters.FilterSet):
    """Filter for events"""
    search = filters.CharFilter(method='filter_search')
    category = filters.UUIDFilter(field_name='category__id')
    category_slug = filters.CharFilter(field_name='category__slug')
    tag = filters.CharFilter(field_name='tags__slug')
    organizer = filters.UUIDFilter(field_name='organizer__id')
    event_type = filters.ChoiceFilter(choices=Event.EVENT_TYPE_CHOICES)
    status = filters.ChoiceFilter(choices=Event.STATUS_CHOICES)
    date_from = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='end_date', lookup_expr='lte')
    is_virtual = filters.BooleanFilter()
    is_free = filters.BooleanFilter()
    is_featured = filters.BooleanFilter()
    location = filters.CharFilter(
        field_name='location', lookup_expr='icontains')
    city = filters.CharFilter(field_name='city', lookup_expr='icontains')
    region = filters.CharFilter(field_name='region', lookup_expr='icontains')

    class Meta:
        model = Event
        fields = [
            'search', 'category', 'category_slug', 'tag', 'organizer',
            'event_type', 'status', 'date_from', 'date_to',
            'is_virtual', 'is_free', 'is_featured', 'location', 'city', 'region'
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(organizer__username__icontains=value) |
            Q(organizer__first_name__icontains=value) |
            Q(organizer__last_name__icontains=value) |
            Q(organization_name__icontains=value)
        )


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for events with full CRUD and registration features"""
    queryset = Event.objects.select_related('organizer', 'category').prefetch_related(
        'speakers', 'sponsors', 'gallery_images'
    ).annotate(
        registrations_count=Count('registrations', distinct=True)
    )
    filterset_class = EventFilter
    search_fields = ['title', 'description',
                     'organization_name', 'organizer__username']
    ordering_fields = [
        'start_date', 'end_date', 'created_at', 'views_count',
        'likes_count', 'shares_count', 'registration_count', 'price'
    ]
    ordering = ['start_date']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventListSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action in ['publish', 'cancel']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        # Filter upcoming/past events
        if self.action == 'upcoming':
            queryset = queryset.filter(start_date__gte=timezone.now())
        elif self.action == 'past':
            queryset = queryset.filter(end_date__lt=timezone.now())

        return queryset

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Get event details and track view"""
        instance = self.get_object()

        # Track view if user is authenticated
        if request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Event)
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
    def register(self, request, slug=None):
        """Register for an event"""
        event = self.get_object()

        # Check if event is open for registration
        if event.status != 'published':
            return Response(
                {'detail': 'Event is not open for registration'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if event.registration_deadline and timezone.now() > event.registration_deadline:
            return Response(
                {'detail': 'Registration deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if event.max_attendees and event.registration_count >= event.max_attendees:
            return Response(
                {'detail': 'Event is fully booked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already registered
        if EventRegistration.objects.filter(event=event, user=request.user).exists():
            return Response(
                {'detail': 'You are already registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create registration
        serializer = EventRegistrationCreateSerializer(
            data=request.data,
            context={'request': request, 'event': event}
        )
        if serializer.is_valid():
            registration = serializer.save()
            return Response(
                EventRegistrationSerializer(registration).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unregister(self, request, slug=None):
        """Cancel registration for an event"""
        event = self.get_object()

        try:
            registration = EventRegistration.objects.get(
                event=event, user=request.user)
            registration.status = 'cancelled'
            registration.save()

            # Update event registration count
            event.registration_count = F('registration_count') - 1
            event.save(update_fields=['registration_count'])

            return Response({'detail': 'Registration cancelled successfully'})
        except EventRegistration.DoesNotExist:
            return Response(
                {'detail': 'You are not registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def registrations(self, request, slug=None):
        """Get event registrations (organizer only)"""
        event = self.get_object()

        # Check permission
        if event.organizer != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to view registrations'},
                status=status.HTTP_403_FORBIDDEN
            )

        registrations = event.registrations.select_related('user')
        page = self.paginate_queryset(registrations)
        if page is not None:
            serializer = EventRegistrationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        """Like or unlike an event"""
        event = self.get_object()
        content_type = ContentType.objects.get_for_model(Event)

        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=event.id
        )

        if not created:
            like.delete()
            event.likes_count = F('likes_count') - 1
            event.save(update_fields=['likes_count'])
            return Response({'liked': False, 'likes_count': event.likes_count})

        event.likes_count = F('likes_count') + 1
        event.save(update_fields=['likes_count'])
        return Response({'liked': True, 'likes_count': event.likes_count})

    @action(detail=True, methods=['post'])
    def bookmark(self, request, slug=None):
        """Bookmark or unbookmark an event"""
        event = self.get_object()
        content_type = ContentType.objects.get_for_model(Event)

        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=event.id
        )

        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})

        return Response({'bookmarked': True})

    @action(detail=True, methods=['post'])
    def share(self, request, slug=None):
        """Share an event"""
        event = self.get_object()
        platform = request.data.get('platform', 'internal')

        content_type = ContentType.objects.get_for_model(Event)
        share = Share.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=event.id,
            platform=platform
        )

        event.shares_count = F('shares_count') + 1
        event.save(update_fields=['shares_count'])

        return Response({
            'shared': True,
            'shares_count': event.shares_count,
            'share_id': share.id
        })

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events"""
        events = self.get_queryset()
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get past events"""
        events = self.get_queryset()
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's events"""
        today = timezone.now().date()
        events = self.get_queryset().filter(
            start_date__date__lte=today,
            end_date__date__gte=today
        )
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured events"""
        events = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular events based on registrations"""
        events = self.get_queryset().order_by('-registration_count')[:20]
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get events organized by the current user"""
        events = self.get_queryset().filter(organizer=request.user)
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def registered(self, request):
        """Get events the user is registered for"""
        registrations = EventRegistration.objects.filter(
            user=request.user,
            status='confirmed'
        ).select_related('event')
        events = [reg.event for reg in registrations]

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish(self, request, slug=None):
        """Publish a draft event (staff only)"""
        event = self.get_object()
        if event.status == 'published':
            return Response({'detail': 'Event is already published'}, status=status.HTTP_400_BAD_REQUEST)

        event.status = 'published'
        event.save()

        serializer = self.get_serializer(event)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, slug=None):
        """Cancel an event"""
        event = self.get_object()

        # Check permission
        if event.organizer != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to cancel this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        event.status = 'cancelled'
        event.save()

        # TODO: Send notifications to registered users

        serializer = self.get_serializer(event)
        return Response(serializer.data)


class EventSpeakerViewSet(viewsets.ModelViewSet):
    """ViewSet for event speakers"""
    queryset = EventSpeaker.objects.select_related('event')
    serializer_class = EventSpeakerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        event_id = self.request.query_params.get('event')
        if event_id:
            queryset = queryset.filter(event__id=event_id)
        return queryset


class EventSponsorViewSet(viewsets.ModelViewSet):
    """ViewSet for event sponsors"""
    queryset = EventSponsor.objects.select_related('event')
    serializer_class = EventSponsorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        event_id = self.request.query_params.get('event')
        if event_id:
            queryset = queryset.filter(event__id=event_id)
        return queryset


class EventRegistrationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing user's event registrations"""
    queryset = EventRegistration.objects.select_related('event', 'user')
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own registrations
        return super().get_queryset().filter(user=self.request.user)
