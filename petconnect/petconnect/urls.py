"""URL configuration for PetConnect."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('feed.urls')),
    path('accounts/', include('accounts.urls')),
    path('pets/', include('pets.urls')),
    path('chat/', include('chat.urls')),
    path('playdates/', include('playdates.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])



