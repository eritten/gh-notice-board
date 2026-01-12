from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Event, EventRegistration, EventImage, EventSpeaker, EventSponsor, EventReminder
from authentication.serializers import UserMinimalSerializer
from tags.serializers import TagSerializer, CategorySerializer
from interactions.models import Like, Comment, Share, View, Bookmark
from .models import Event, EventCategory, EventRegistration, EventImage, EventSpeaker, EventSponsor, EventReminder
User = get_user_model()


class EventCategorySerializer(serializers.ModelSerializer):
    """Serializer for event categories"""
    events_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'color',
                  'is_active', 'order', 'events_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class EventMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for events (for use in other apps like newsletters)"""
    organizer = UserMinimalSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)


class EventSpeakerSerializer(serializers.ModelSerializer):
    """Serializer for event speakers"""

    class Meta:
        model = EventSpeaker
        fields = [
            'id', 'name', 'title', 'bio', 'photo', 'linkedin_url',
            'twitter_username', 'website', 'order'
        ]


class EventSponsorSerializer(serializers.ModelSerializer):
    """Serializer for event sponsors"""

    class Meta:
        model = EventSponsor
        fields = [
            'id', 'name', 'logo', 'website', 'description',
            'sponsorship_level', 'order'
        ]


class EventImageSerializer(serializers.ModelSerializer):
    """Serializer for event gallery images"""

    class Meta:
        model = EventImage
        fields = ['id', 'image', 'caption', 'is_cover', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for event registrations"""
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'user', 'registration_type', 'ticket_number',
            'attendance_status', 'checked_in_at', 'special_requirements',
            'is_speaker', 'is_vip', 'created_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'created_at']


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event lists"""
    organizer = UserMinimalSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Engagement and status
    user_registered = serializers.SerializerMethodField()
    user_liked = serializers.SerializerMethodField()
    user_bookmarked = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    is_ongoing = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    days_until = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image',
            'category', 'tags', 'organizer', 'venue_name', 'venue_address',
            'event_type', 'start_date', 'end_date', 'timezone',
            'is_featured', 'is_trending', 'status',
            'registration_required', 'max_attendees', 'registered_count',
            'views_count', 'likes_count', 'shares_count',
            'user_registered', 'user_liked', 'user_bookmarked',
            'is_upcoming', 'is_ongoing', 'is_past', 'days_until',
            'price', 'early_bird_price', 'early_bird_deadline',
            'created_at', 'updated_at'
        ]

    def get_user_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return EventRegistration.objects.filter(
                user=request.user,
                event=obj,
                status='confirmed'
            ).exists()
        return False

    def get_user_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False

    def get_user_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Bookmark.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
            ).exists()
        return False

    def get_is_upcoming(self, obj):
        return obj.is_upcoming

    def get_is_ongoing(self, obj):
        return obj.is_ongoing

    def get_is_past(self, obj):
        return obj.is_past

    def get_days_until(self, obj):
        return obj.days_until_event()


class EventDetailSerializer(EventListSerializer):
    """Detailed serializer for event view"""
    speakers = EventSpeakerSerializer(many=True, read_only=True)
    sponsors = EventSponsorSerializer(many=True, read_only=True)
    gallery_images = EventImageSerializer(many=True, read_only=True)

    # Registration details
    registration_list = serializers.SerializerMethodField()
    related_events = serializers.SerializerMethodField()

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            'description', 'agenda', 'venue_details', 'venue_map_url',
            'virtual_meeting_url', 'virtual_meeting_password',
            'registration_instructions', 'cancellation_policy',
            'covid_safety_measures', 'parking_info', 'accessibility_info',
            'contact_email', 'contact_phone', 'website_url',
            'facebook_event_url', 'livestream_url',
            'speakers', 'sponsors', 'gallery_images',
            'registration_list', 'related_events',
            'is_cancelled', 'cancellation_reason',
            'allow_waitlist', 'waitlist_count',
            'check_in_code', 'certificate_template'
        ]

    def get_registration_list(self, obj):
        # Only show to organizer or admin
        request = self.context.get('request')
        if request and (request.user == obj.organizer or request.user.is_staff):
            registrations = EventRegistration.objects.filter(
                event=obj,
                status='confirmed'
            ).select_related('user')[:10]  # Limit to 10 for performance

            return EventRegistrationSerializer(
                registrations,
                many=True,
                context=self.context
            ).data
        return []

    def get_related_events(self, obj):
        # Get related events based on category and tags
        related = Event.objects.filter(
            status='published',
            category=obj.category,
            is_cancelled=False
        ).exclude(id=obj.id)[:5]

        return EventListSerializer(
            related,
            many=True,
            context=self.context
        ).data


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating events"""
    tags_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    speakers_data = EventSpeakerSerializer(many=True, required=False)
    sponsors_data = EventSponsorSerializer(many=True, required=False)
    gallery_images = EventImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'title', 'summary', 'description', 'agenda',
            'category', 'tags_ids', 'featured_image',
            'venue_name', 'venue_address', 'venue_details', 'venue_map_url',
            'event_type', 'start_date', 'end_date', 'timezone',
            'virtual_meeting_url', 'virtual_meeting_password',
            'registration_required', 'max_attendees', 'allow_waitlist',
            'price', 'early_bird_price', 'early_bird_deadline',
            'registration_instructions', 'cancellation_policy',
            'covid_safety_measures', 'parking_info', 'accessibility_info',
            'contact_email', 'contact_phone', 'website_url',
            'facebook_event_url', 'livestream_url',
            'is_featured', 'is_trending', 'status',
            'speakers_data', 'sponsors_data', 'gallery_images', 'uploaded_images'
        ]

    def create(self, validated_data):
        tags_ids = validated_data.pop('tags_ids', [])
        speakers_data = validated_data.pop('speakers_data', [])
        sponsors_data = validated_data.pop('sponsors_data', [])
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Create the event
        event = Event.objects.create(
            organizer=self.context['request'].user,
            **validated_data
        )

        # Add tags
        if tags_ids:
            from tags.models import Tag, ContentTag
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='event',
                    object_id=event.id,
                    created_by=self.context['request'].user
                )
                tag.increment_usage()

        # Add speakers
        for speaker_data in speakers_data:
            EventSpeaker.objects.create(event=event, **speaker_data)

        # Add sponsors
        for sponsor_data in sponsors_data:
            EventSponsor.objects.create(event=event, **sponsor_data)

        # Add gallery images
        for index, image in enumerate(uploaded_images):
            EventImage.objects.create(
                event=event,
                image=image,
                order=index
            )

        return event

    def update(self, instance, validated_data):
        tags_ids = validated_data.pop('tags_ids', None)
        speakers_data = validated_data.pop('speakers_data', None)
        sponsors_data = validated_data.pop('sponsors_data', None)
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Update event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_ids is not None:
            from tags.models import Tag, ContentTag
            # Remove existing tags
            ContentTag.objects.filter(
                content_type='event',
                object_id=instance.id
            ).delete()

            # Add new tags
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='event',
                    object_id=instance.id,
                    created_by=self.context['request'].user
                )

        # Update speakers if provided
        if speakers_data is not None:
            instance.speakers.all().delete()
            for speaker_data in speakers_data:
                EventSpeaker.objects.create(event=instance, **speaker_data)

        # Update sponsors if provided
        if sponsors_data is not None:
            instance.sponsors.all().delete()
            for sponsor_data in sponsors_data:
                EventSponsor.objects.create(event=instance, **sponsor_data)

        # Add new gallery images
        for index, image in enumerate(uploaded_images):
            EventImage.objects.create(
                event=instance,
                image=image,
                order=instance.gallery_images.count() + index
            )

        return instance


class EventRegistrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating event registrations"""

    class Meta:
        model = EventRegistration
        fields = [
            'event', 'registration_type', 'special_requirements',
            'accept_terms'
        ]

    def validate_event(self, value):
        if value.status != 'published':
            raise serializers.ValidationError(
                "Event is not available for registration.")

        if value.is_cancelled:
            raise serializers.ValidationError("Event has been cancelled.")

        if value.is_past:
            raise serializers.ValidationError(
                "Cannot register for past events.")

        if value.registration_required and value.is_full() and not value.allow_waitlist:
            raise serializers.ValidationError("Event is full.")

        return value

    def validate_accept_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must accept the terms to register.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        event = validated_data['event']

        # Check if already registered
        if EventRegistration.objects.filter(user=user, event=event).exists():
            raise serializers.ValidationError(
                "You are already registered for this event.")

        # Generate ticket number
        import random
        import string
        ticket_number = f"{event.slug.upper()}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

        # Determine status
        status = 'waitlisted' if event.is_full() else 'confirmed'

        registration = EventRegistration.objects.create(
            user=user,
            ticket_number=ticket_number,
            status=status,
            **validated_data
        )

        # Update event counts
        if status == 'confirmed':
            event.registered_count += 1
        else:
            event.waitlist_count += 1
        event.save()

        return registration


class EventEngagementSerializer(serializers.Serializer):
    """Serializer for event engagement actions"""
    action = serializers.ChoiceField(
        choices=['like', 'unlike', 'bookmark', 'unbookmark'])

    def save(self):
        event = self.context['view'].get_object()
        user = self.context['request'].user
        action = self.validated_data['action']
        content_type = ContentType.objects.get_for_model(event)

        if action == 'like':
            Like.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=event.id
            )
            event.likes_count += 1
        elif action == 'unlike':
            Like.objects.filter(
                user=user,
                content_type=content_type,
                object_id=event.id
            ).delete()
            event.likes_count = max(0, event.likes_count - 1)
        elif action == 'bookmark':
            Bookmark.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=event.id
            )
            event.bookmarks_count += 1
        elif action == 'unbookmark':
            Bookmark.objects.filter(
                user=user,
                content_type=content_type,
                object_id=event.id
            ).delete()
            event.bookmarks_count = max(0, event.bookmarks_count - 1)

        event.save()
        return event


class EventReminderSerializer(serializers.ModelSerializer):
    """Serializer for event reminders"""

    class Meta:
        model = EventReminder
        fields = [
            'id', 'event', 'subject', 'message', 'send_at',
            'is_sent', 'sent_at', 'created_at'
        ]
        read_only_fields = ['id', 'is_sent', 'sent_at', 'created_at']


class EventCheckInSerializer(serializers.Serializer):
    """Serializer for event check-in"""
    ticket_number = serializers.CharField()

    def validate_ticket_number(self, value):
        try:
            registration = EventRegistration.objects.get(ticket_number=value)
            if registration.status != 'confirmed':
                raise serializers.ValidationError("Invalid ticket status.")
            if registration.attendance_status == 'checked_in':
                raise serializers.ValidationError("Already checked in.")
        except EventRegistration.DoesNotExist:
            raise serializers.ValidationError("Invalid ticket number.")
        return value

    def save(self):
        ticket_number = self.validated_data['ticket_number']
        registration = EventRegistration.objects.get(
            ticket_number=ticket_number)
        registration.attendance_status = 'checked_in'
        registration.checked_in_at = timezone.now()
        registration.save()
        return registration
