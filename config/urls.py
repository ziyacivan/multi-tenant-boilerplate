from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from employees.views import EmployeeViewSet
from teams.views import TeamViewSet
from titles.views import TitleViewSet

tenant_router = DefaultRouter()
tenant_router.register(r"employees", EmployeeViewSet, basename="employee")
tenant_router.register(r"titles", TitleViewSet, basename="title")
tenant_router.register(r"teams", TeamViewSet, basename="team")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("config.public_urls")),
    path("api/v1/", include(tenant_router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
