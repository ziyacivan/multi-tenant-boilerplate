from django.contrib import admin
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from employees.views import EmployeeViewSet

tenant_router = DefaultRouter()
tenant_router.register(r"employees", EmployeeViewSet, basename="employee")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("config.public_urls")),
    path("api/v1/", include(tenant_router.urls)),
]
