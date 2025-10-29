from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from tenants.views import ClientViewSet

public_router = DefaultRouter()
public_router.register(r"clients", ClientViewSet)

urlpatterns = [
    path(
        "api/v1/",
        include(
            [
                path("auth/", include("auth.urls")),
                path("schema/", SpectacularAPIView.as_view(), name="schema"),
                path(
                    "schema/swagger-ui/",
                    SpectacularSwaggerView.as_view(url="/api/v1/schema/"),
                    name="swagger-ui",
                ),
                path(
                    "schema/redoc/",
                    SpectacularRedocView.as_view(url="/api/v1/schema/"),
                    name="redoc",
                ),
            ]
            + public_router.urls
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
