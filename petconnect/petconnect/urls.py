"""URL configuration for PetConnect."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

service_worker = cache_control(max_age=0, no_cache=True)(
    TemplateView.as_view(
        template_name="sw.js",
        content_type="application/javascript",
        extra_context={"version": "2.1.0"},
    )
)


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", include("feed.urls")),
    path("accounts/", include("accounts.urls")),
    path("pets/", include("pets.urls")),
    path("chat/", include("chat.urls")),
    path("playdates/", include("playdates.urls")),
    path("sw.js", service_worker, name="service_worker"),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
