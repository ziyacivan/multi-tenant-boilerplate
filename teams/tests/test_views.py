from django.urls import reverse

from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from rest_framework import status

from employees.choices import EmployeeRole
from teams.models import Team
from utils.tests.mixins import AuthenticatedTenantTestMixin


class TeamViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb teams.tests.test_views.TeamViewSetTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        super().setUp()
        self.list_url = reverse("team-list")

        self.authenticate_client(role=EmployeeRole.manager)

        baker.make(Team, _quantity=5)

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
        team = Team.objects.first()
        url = reverse("team-detail", args=[team.id])
        response = self.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], team.id)

    def test_retrieve_not_found(self):
        url = reverse("team-detail", args=[999])
        response = self.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_success(self):
        team = Team.objects.first()
        url = reverse("team-detail", args=[team.id])
        data = {"name": "Updated Team Name"}
        response = self.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Team Name")

        team.refresh_from_db()
        self.assertEqual(team.name, "Updated Team Name")

    def test_partial_update_unauthorized(self):
        self.authenticate_client(role=EmployeeRole.employee)
        team = Team.objects.first()
        url = reverse("team-detail", args=[team.id])
        data = {"name": "Attempted Update"}
        response = self.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        team.refresh_from_db()
        self.assertNotEqual(team.name, "Attempted Update")

    def test_delete_success(self):
        team = Team.objects.first()
        url = reverse("team-detail", args=[team.id])
        response = self.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(id=team.id).first().is_active)

    def test_delete_unauthorized(self):
        self.authenticate_client(role=EmployeeRole.employee)
        team = Team.objects.first()
        url = reverse("team-detail", args=[team.id])
        response = self.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(Team.objects.filter(id=team.id).first().is_active)

    def test_delete_not_found(self):
        url = reverse("team-detail", args=[999])
        response = self.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_success(self):
        data = {"name": "New Team"}
        response = self.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Team")
        self.assertTrue(Team.objects.filter(name="New Team").exists())

    def test_create_unauthorized(self):
        self.authenticate_client(role=EmployeeRole.employee)
        data = {"name": "Unauthorized Team"}
        response = self.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Team.objects.filter(name="Unauthorized Team").exists())

    def test_create_name_unique_constraint(self):
        existing_team = Team.objects.first()
        data = {"name": existing_team.name}  # Duplicate name
        response = self.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
