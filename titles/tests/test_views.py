from django.urls import reverse

from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from rest_framework import status

from employees.choices import EmployeeRole
from titles.models import Title
from utils.tests.mixins import AuthenticatedTenantTestMixin


class TitleViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb titles.tests.test_views.TitleViewSetTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        super().setUp()
        self.list_url = reverse("title-list")

        self.authenticate_client(role=EmployeeRole.manager)

        baker.make(Title, _quantity=5)

    def test_list_success(self):
        response = self.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 5)

    def test_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_success(self):
        title = Title.objects.first()
        url = reverse("title-detail", args=[title.id])
        response = self.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], title.id)

    def test_retrieve_not_found(self):
        url = reverse("title-detail", args=[999])
        response = self.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_success(self):
        title = Title.objects.first()
        url = reverse("title-detail", args=[title.id])
        data = {"name": "Updated Title Name"}
        response = self.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        title.refresh_from_db()
        self.assertEqual(title.name, "Updated Title Name")

    def test_partial_update_unauthorized(self):
        self.authenticate_client(role=EmployeeRole.employee)
        title = Title.objects.first()
        url = reverse("title-detail", args=[title.id])
        data = {"name": "Updated Title Name"}
        response = self.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_name_unique_constraint(self):
        titles = Title.objects.all()[:2]
        url = reverse("title-detail", args=[titles[0].id])
        data = {"name": titles[1].name}  # Duplicate name
        response = self.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_delete_success(self):
        title = Title.objects.first()
        url = reverse("title-detail", args=[title.id])
        response = self.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Title.objects.filter(id=title.id).first().is_active)

    def test_delete_unauthorized(self):
        self.authenticate_client(role=EmployeeRole.employee)
        title = Title.objects.first()
        url = reverse("title-detail", args=[title.id])
        response = self.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_success(self):
        data = {"name": "New Title"}
        response = self.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Title.objects.filter(name="New Title").count(), 1)

    def test_create_unauthorized(self):
        self.authenticate_client(role=EmployeeRole.employee)
        data = {"name": "New Title"}
        response = self.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_name_unique_constraint(self):
        existing_title = Title.objects.first()
        data = {"name": existing_title.name}  # Duplicate name
        response = self.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
