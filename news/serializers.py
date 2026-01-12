from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import NewsArticle, NewsImage, NewsRevision
from authentication.serializers import UserMinimalSerializer
from tags.serializers import TagSerializer, CategorySerializer
from interactions.models import Like, Comment, Share, View, Bookmark

User = get_user_model()


class NewsImageSerializer(serializers.ModelSerializer):
    """Serializer for news gallery images"""

    class Meta:
        model = NewsImage
        fields = ['id', 'image', 'caption', 'credit', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class NewsRevisionSerializer(serializers.ModelSerializer):
    """Serializer for news article revisions"""
    revision_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = NewsRevision
        fields = [
            'id', 'title', 'content', 'summary', 'revision_by',
            'revision_note', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NewsArticleMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for news articles (for use in other apps like newsletters)"""
    author = UserMinimalSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    reading_time = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image',
            'category', 'author', 'is_breaking', 'is_featured',
            'views_count', 'likes_count', 'reading_time',
            'published_at', 'created_at'
        ]
        read_only_fields = fields

    def get_reading_time(self, obj):
        return obj.get_reading_time()


class NewsArticleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for news article lists"""
    author = UserMinimalSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Engagement counts
    user_liked = serializers.SerializerMethodField()
    user_bookmarked = serializers.SerializerMethodField()
    reading_time = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image',
            'category', 'tags', 'author', 'source',
            'status', 'is_breaking', 'is_featured', 'is_trending',
            'views_count', 'likes_count', 'comments_count', 'shares_count',
            'user_liked', 'user_bookmarked', 'reading_time', 'is_new',
            'published_at', 'created_at'
        ]

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

    def get_reading_time(self, obj):
        return obj.get_reading_time()

    def get_is_new(self, obj):
        return obj.is_new


class NewsArticleDetailSerializer(NewsArticleListSerializer):
    """Detailed serializer for news article view"""
    gallery_images = NewsImageSerializer(many=True, read_only=True)
    published_by = UserMinimalSerializer(read_only=True)

    # Related content
    related_articles = serializers.SerializerMethodField()

    class Meta(NewsArticleListSerializer.Meta):
        fields = NewsArticleListSerializer.Meta.fields + [
            'content', 'meta_title', 'meta_description', 'keywords',
            'image_caption', 'image_credit', 'location', 'source_url',
            'is_exclusive', 'is_ai_generated', 'ai_summary',
            'gallery_images', 'published_by', 'related_articles',
            'allow_comments', 'require_comment_approval',
            'updated_at', 'breaking_expires_at'
        ]

    def get_related_articles(self, obj):
        # Get related articles based on category and tags
        related = NewsArticle.objects.filter(
            status='published',
            category=obj.category
        ).exclude(id=obj.id)[:5]

        return NewsArticleListSerializer(
            related,
            many=True,
            context=self.context
        ).data


class NewsArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating news articles"""
    tags_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    gallery_images = NewsImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = NewsArticle
        fields = [
            'title', 'summary', 'content', 'meta_title', 'meta_description',
            'keywords', 'category', 'tags_ids', 'featured_image',
            'image_caption', 'image_credit', 'source', 'source_url',
            'location', 'status', 'is_breaking', 'is_featured',
            'is_trending', 'is_exclusive', 'allow_comments',
            'require_comment_approval', 'gallery_images', 'uploaded_images'
        ]

    def create(self, validated_data):
        tags_ids = validated_data.pop('tags_ids', [])
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Create the article
        article = NewsArticle.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        # Add tags
        if tags_ids:
            from tags.models import Tag
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                from tags.models import ContentTag
                ContentTag.objects.create(
                    tag=tag,
                    content_type='news',
                    object_id=article.id,
                    created_by=self.context['request'].user
                )
                tag.increment_usage()

        # Add gallery images
        for index, image in enumerate(uploaded_images):
            NewsImage.objects.create(
                article=article,
                image=image,
                order=index
            )

        return article

    def update(self, instance, validated_data):
        tags_ids = validated_data.pop('tags_ids', None)
        uploaded_images = validated_data.pop('uploaded_images', [])

        # Update article fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_ids is not None:
            from tags.models import Tag, ContentTag
            # Remove existing tags
            ContentTag.objects.filter(
                content_type='news',
                object_id=instance.id
            ).delete()

            # Add new tags
            tags = Tag.objects.filter(id__in=tags_ids)
            for tag in tags:
                ContentTag.objects.create(
                    tag=tag,
                    content_type='news',
                    object_id=instance.id,
                    created_by=self.context['request'].user
                )

        # Add new gallery images
        for index, image in enumerate(uploaded_images):
            NewsImage.objects.create(
                article=instance,
                image=image,
                order=instance.gallery_images.count() + index
            )

        return instance


class NewsEngagementSerializer(serializers.Serializer):
    """Serializer for news engagement actions"""
    action = serializers.ChoiceField(
        choices=['like', 'unlike', 'bookmark', 'unbookmark'])

    def save(self):
        article = self.context['view'].get_object()
        user = self.context['request'].user
        action = self.validated_data['action']
        content_type = ContentType.objects.get_for_model(article)

        if action == 'like':
            Like.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=article.id
            )
            article.likes_count += 1
        elif action == 'unlike':
            Like.objects.filter(
                user=user,
                content_type=content_type,
                object_id=article.id
            ).delete()
            article.likes_count = max(0, article.likes_count - 1)
        elif action == 'bookmark':
            Bookmark.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=article.id
            )
            article.bookmarks_count += 1
        elif action == 'unbookmark':
            Bookmark.objects.filter(
                user=user,
                content_type=content_type,
                object_id=article.id
            ).delete()
            article.bookmarks_count = max(0, article.bookmarks_count - 1)

        article.save()
        return article
