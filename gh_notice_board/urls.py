from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('authentication.urls')),
    path('api/', include('ai_service.urls')),
    path('api/', include('tags.urls')),
    path('api/', include('interactions.urls')),
    path('api/', include('news.urls')),
    path('api/', include('events.urls')),
    path('api/', include('opportunities.urls')),
    path('api/', include('announcements.urls')),
    path('api/', include('diaspora.urls')),
    path('api/', include('submissions.urls')),
    path('api/', include('newsletters.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
