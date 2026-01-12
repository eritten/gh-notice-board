from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Opportunity, Application, SavedOpportunity, OpportunityAlert
from .serializers import (
    OpportunityListSerializer, OpportunityDetailSerializer,
    ApplicationSerializer, ApplicationCreateSerializer,
    SavedOpportunitySerializer, OpportunityAlertSerializer
)


class OpportunityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Opportunity.objects.filter(
        status='published').select_related('category', 'posted_by')
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['opportunity_type', 'category__slug',
                        'is_featured', 'is_remote', 'is_diaspora']
    search_fields = ['title', 'description', 'organization_name', 'location']
    ordering_fields = ['published_at', 'deadline', 'views_count', 'created_at']
    ordering = ['-published_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OpportunityDetailSerializer
        return OpportunityListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        opportunities = self.get_queryset().filter(is_featured=True)[:5]
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get opportunities with upcoming deadlines"""
        today = timezone.now()
        opportunities = self.get_queryset().filter(
            deadline__gte=today
        ).order_by('deadline')[:20]
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def jobs(self, request):
        opportunities = self.get_queryset().filter(opportunity_type='job')
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def scholarships(self, request):
        opportunities = self.get_queryset().filter(opportunity_type='scholarship')
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def diaspora(self, request):
        opportunities = self.get_queryset().filter(is_diaspora=True)
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.select_related('opportunity', 'applicant')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['opportunity', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Application.objects.all()
        return Application.objects.filter(applicant=self.request.user)

    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        # Increment applications count for the opportunity
        opportunity = application.opportunity
        opportunity.applications_count += 1
        opportunity.save(update_fields=['applications_count'])


class SavedOpportunityViewSet(viewsets.ModelViewSet):
    queryset = SavedOpportunity.objects.select_related('opportunity')
    serializer_class = SavedOpportunitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedOpportunity.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
