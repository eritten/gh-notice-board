from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsArticleViewSet, NewsRevisionViewSet

router = DefaultRouter()
router.register(r'articles', NewsArticleViewSet, basename='news-article')
router.register(r'revisions', NewsRevisionViewSet, basename='news-revision')

app_name = 'news'

urlpatterns = [
    path('', include(router.urls)),
]
