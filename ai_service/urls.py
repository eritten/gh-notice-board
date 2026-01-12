from django.urls import path
from .views import (
    ContentAnalysisView,
    ContentSuggestionsView,
    ContentModerationView,
    SmartSummarizationView
)

urlpatterns = [
    path('ai/analyze/', ContentAnalysisView.as_view(), name='content-analysis'),
    path('ai/suggestions/', ContentSuggestionsView.as_view(), name='content-suggestions'),
    path('ai/moderate/', ContentModerationView.as_view(), name='content-moderation'),
    path('ai/summarize/', SmartSummarizationView.as_view(), name='content-summarization'),
]
