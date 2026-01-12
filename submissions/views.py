from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import ContentSubmission, ContactMessage
from .serializers import (
    ContentSubmissionListSerializer, ContentSubmissionDetailSerializer,
    ContentSubmissionCreateSerializer, ContactMessageSerializer,
    ContactMessageCreateSerializer
)


class ContentSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ContentSubmission.objects.all()
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['submission_type', 'status', 'priority']
    search_fields = ['title', 'content', 'submitter_name', 'submitter_email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ContentSubmissionCreateSerializer
        elif self.action == 'retrieve':
            return ContentSubmissionDetailSerializer
        return ContentSubmissionListSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ContentSubmission.objects.all()
        if self.request.user.is_authenticated:
            return ContentSubmission.objects.filter(submitted_by=self.request.user)
        return ContentSubmission.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'Submission received successfully. We will review it shortly.'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending submissions"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        submissions = self.get_queryset().filter(status='submitted')
        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a submission"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        submission = self.get_object()
        submission.approve(request.user)
        return Response({'message': 'Submission approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a submission"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        submission = self.get_object()
        reason = request.data.get('reason', '')
        submission.reject(request.user, reason)
        return Response({'message': 'Submission rejected'})


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['inquiry_type',
                        'is_read', 'is_responded', 'is_resolved']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ContactMessageCreateSerializer
        return ContactMessageSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ContactMessage.objects.all()
        return ContactMessage.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'Message sent successfully. We will get back to you soon.'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        message = self.get_object()
        message.mark_read(request.user)
        return Response({'message': 'Marked as read'})

    @action(detail=True, methods=['post'])
    def mark_responded(self, request, pk=None):
        """Mark message as responded"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        message = self.get_object()
        message.mark_responded()
        return Response({'message': 'Marked as responded'})
