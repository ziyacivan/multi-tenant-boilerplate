---
applyTo: '**'
---
## Copilot Instructions
Bu dosya, GitHub Copilot'un bu proje (HRM API) için kod önerileri üretirken uyması gereken kuralları ve standartları tanımlar. Copilot, bu talimatları kullanarak tutarlı, kaliteli ve proje standartlarına uygun kod önerileri sunmalıdır.

## Genel Kurallar
- **Dil:** Tüm kod önerileri Türkçe yorumlar ve dokümantasyon içermelidir (proje Türkçe dil desteği ile geliştirilmektedir).
- **Kod Kalitesi:** Önerilen kodlar okunabilir, sürdürülebilir ve performanslı olmalıdır. Gereksiz karmaşıklık kaçınılmalıdır.
- **Test Odaklı Geliştirme:** Her yeni fonksiyon veya sınıf için test önerisi sun. Mevcut test kalıplarını takip et (örneğin, TenantTestCaseMixin kullanımı).
- **Hata Yönetimi:** Uygun exception handling öner. Proje spesifik exception'ları kullan (örneğin, BaseAPIException alt sınıfları).
- **Dokümantasyon:** Fonksiyonlar ve sınıflar için docstring'ler ekle. API endpoint'leri için DRF'nin extend_schema dekoratörünü kullan.
- **Güvenlik:** Hassas veriler (şifreler, token'lar) için uygun validasyon ve şifreleme öner.
- **Performans:** Veritabanı sorgularında N+1 problemi önle. Select_related ve prefetch_related kullan.

## Kodlama Standartları
- **Formatlama:** Black (line-length: 88, target-version: py313) standartlarına uy. Tüm öneriler Black formatında olmalıdır.
- **Import Sıralaması:** isort (profile: black) kurallarına göre:
    - Standart kütüphane
    - Django
    - Üçüncü parti
    - İlk parti (auth, config, employees, tenants, users, utils)
    - Yerel klasör
- **Naming Conventions:**
    - Sınıflar: PascalCase
    - Fonksiyonlar: snake_case
    - Değişkenler: snake_case
    - Sabitler: UPPER_CASE
- **Line Length:** 88 karakteri aşma.
- **Docstrings:** Google style docstrings kullan.
- **Type Hints:** Mümkün olduğunca type hints ekle (Python 3.13+ uyumlu).

## Teknoloji Stack ve Mimari
- **Framework:** Django 5.2.7, DRF (djangorestframework), django-tenants (çok kiracılı mimari).
- **Authentication:** JWT (djangorestframework-simplejwt).
- **Database:** PostgreSQL, çok kiracılı schema'lar.
- **Asynchronous Tasks:** Celery + Redis.
- **Email:** Django email backend, SendGrid entegrasyonu.
- **Testing:** Django test framework, model-bakery, coverage (modül bazlı minimum %'ler: auth:85, tenants:80, users:75, employees:80, utils:90).
- **Deployment:** Docker, docker-compose.
- **CI/CD:** GitHub Actions (formatting check, paralel modül testleri, coverage kontrolü).

## Tenant-Aware Kodlama
- Tüm modeller ve sorgular tenant context'inde çalışmalıdır. `tenant_context()` kullan.
- Public schema (shared apps) ve tenant schema'ları (tenant apps) ayırımı yap.
- Kullanıcı işlemleri için TenantUser modelini tercih et.
- Domain routing için CustomTenantMiddleware kullan.

## API Tasarımı
- RESTful API prensipleri takip et.
- Serializer'lar için ModelSerializer kullan.
- Permission'lar: IsAuthenticated, IsMinimumManagerOrReadOnly gibi proje spesifik permission'lar.
- Pagination: PageNumberPagination (page_size: 20).
- Schema dokümantasyonu için drf-spectacular kullan.

## Örnek Kod Kalıpları
Model Örneği
```python
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.models import BaseModel


class Employee(BaseModel):
    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, verbose_name=_("user")
    )
    first_name = models.CharField(_("first name"), max_length=255)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.employee,
    )
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("employee")
        verbose_name_plural = _("employees")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

View Örneği
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from employees.models import Employee
from employees.serializers import EmployeeSerializer
from employees.services import EmployeeService


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-created_on")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    service_class = EmployeeService()

    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )
```

Test Örneği
```python
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker

from employees.models import Employee
from utils.tests.mixins import TenantTestCaseMixin


class EmployeeServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def test_create_object_success(self):
        user = baker.make("users.User")
        employee = self.service.create_object(
            user=user,
            first_name="Jane",
            last_name="Doe",
        )
        self.assertIsNotNone(employee)
        self.assertEqual(employee.user, user)
```

Service Örneği
```python
from utils.interfaces import BaseService


class EmployeeService(BaseService):
    def create_object(self, user, first_name, last_name, **kwargs):
        employee = Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        return employee

    def update_object(self, instance, **kwargs):
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete_object(self, instance):
        instance.delete()
```

## Yasaklar ve Kaçınılması Gerekenler
- **Hardcoded Values:** Konfigürasyon değerlerini .env veya settings'den al.
- **Global State:** Tenant context dışında global değişken kullanma.
- **Raw SQL:** Mümkün olduğunca ORM kullan. Raw SQL zorunluysa açıklama ekle.
- **Magic Numbers/Strings:** Sabitler olarak tanımla.
- **Print Statements:** Logging kullan (Django logging).
- **Direct Database Access:** Service layer üzerinden işlemleri yap.
- **Blocking Operations:** Async task'lar için Celery kullan.
- **Security Vulnerabilities:** SQL injection, XSS vb. riskler önle.
