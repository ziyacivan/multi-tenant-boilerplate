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
                    SpectacularSwaggerView.as_view(url_name="schema"),
                    name="swagger-ui",
                ),
                path(
                    "schema/redoc/",
                    SpectacularRedocView.as_view(url_name="schema"),
                    name="redoc",
                ),
            ]
            + public_router.urls
        ),
    )
]
