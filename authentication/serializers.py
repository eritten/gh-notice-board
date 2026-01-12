from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import UserProfile
from tags.models import Tag

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    interests = serializers.StringRelatedField(many=True, read_only=True)
    interests_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        source='interests'
    )

    class Meta:
        model = UserProfile
        fields = [
            'occupation', 'company', 'skills', 'interests', 'interests_ids',
            'show_email', 'show_location', 'allow_messages', 'theme', 'language',
            'created_at', 'updated_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'display_name', 'bio', 'location', 'website', 'twitter_username',
            'linkedin_url', 'github_username', 'avatar', 'cover_image',
            'is_public', 'email_notifications', 'push_notifications',
            'followers_count', 'following_count', 'posts_count',
            'is_verified', 'verification_badge', 'user_type', 'is_following',
            'created_at', 'updated_at', 'last_seen', 'profile'
        ]
        read_only_fields = [
            'id', 'followers_count', 'following_count', 'posts_count',
            'is_verified', 'verification_badge', 'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_display_name(self, obj):
        return obj.get_display_name()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.is_following(obj)
        return False


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations"""
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'display_name', 'avatar',
            'is_verified', 'verification_badge'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_display_name(self, obj):
        return obj.get_display_name()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Create user profile
        UserProfile.objects.create(user=user)

        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile and related data"""
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create profile
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class FollowSerializer(serializers.Serializer):
    """Serializer for follow/unfollow actions"""
    user_id = serializers.UUIDField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if user == self.context['request'].user:
                raise serializers.ValidationError("You cannot follow yourself.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_posts = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    total_shares = serializers.IntegerField()
    total_views = serializers.IntegerField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    engagement_rate = serializers.FloatField()


class UserActivitySerializer(serializers.Serializer):
    """Serializer for user activity feed"""
    id = serializers.UUIDField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()
    timestamp = serializers.DateTimeField()
    content_type = serializers.CharField()
    content_id = serializers.UUIDField()
    actor = UserMinimalSerializer(read_only=True)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    actor = UserMinimalSerializer(read_only=True)

    class Meta:
        model = User  # Replace with Notification model when created
        fields = [
            'id', 'type', 'title', 'message', 'description', 'actor',
            'is_read', 'created_at', 'link', 'content_type', 'object_id'
        ]
