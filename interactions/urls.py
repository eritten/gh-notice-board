from django.urls import path
from .views import (
    LikeToggleView,
    DislikeToggleView,
    ReviewListCreateView,
    ReviewDetailView,
    BookmarkToggleView,
    BookmarkView,
    InteractionStatsView
)

urlpatterns = [
    # Likes and Dislikes
    path('interactions/like/', LikeToggleView.as_view(), name='like-toggle'),
    path('interactions/dislike/', DislikeToggleView.as_view(), name='dislike-toggle'),

    # Reviews
    path('interactions/reviews/', ReviewListCreateView.as_view(), name='reviews-list-create'),
    path('interactions/reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),

    # Bookmarks
    path('interactions/bookmark/', BookmarkToggleView.as_view(), name='bookmark-toggle'),
    path('interactions/bookmarks/', BookmarkView.as_view(), name='bookmarks'),

    # Statistics
    path('interactions/stats/', InteractionStatsView.as_view(), name='interaction-stats'),
]
