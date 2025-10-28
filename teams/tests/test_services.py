from django_tenants.test.cases import TenantTestCase
from model_bakery import baker

from teams.models import Team
from teams.services import TeamService
from utils.tests.mixins import TenantTestCaseMixin


class TeamServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb teams.tests.test_services.TeamServiceTestCase
    """

    service = TeamService()

    def setUp(self):
        super().setUp()

        self.current_instance = baker.make(
            Team, name="Current Team Instance", description="Current Team Instance"
        )

    def test_create_object(self):
        data = {
            "name": "Test Team",
            "description": "A team for testing purposes.",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)
        self.assertEqual(instance.name, data["name"])
        self.assertEqual(instance.description, data["description"])

    def test_create_object_without_description(self):
        data = {
            "name": "No Description Team",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)
        self.assertEqual(instance.name, data["name"])
        self.assertIsNone(instance.description)

    def test_create_object_unique_constraint(self):
        data = {
            "name": "Current Team Instance",
        }
        with self.assertRaises(Exception):
            self.service.create_object(**data)

    def test_update_object(self):
        data = {
            "name": "Initial Team",
            "description": "Initial Description",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)
        self.assertEqual(instance.name, data["name"])
        self.assertEqual(instance.description, data["description"])

        updated_data = {
            "name": "Updated Team",
            "description": "Updated Description",
        }
        updated_instance = self.service.update_object(instance, **updated_data)
        self.assertIsNotNone(updated_instance)
        self.assertEqual(updated_instance.name, updated_data["name"])
        self.assertEqual(updated_instance.description, updated_data["description"])

    def test_update_object_unique_constraint(self):
        data1 = {
            "name": "First Team",
        }
        instance1 = self.service.create_object(**data1)
        self.assertIsNotNone(instance1)

        data2 = {
            "name": "Second Team",
        }
        instance2 = self.service.create_object(**data2)
        self.assertIsNotNone(instance2)

        with self.assertRaises(Exception):
            self.service.update_object(instance2, name="First Team")

    def test_delete_object(self):
        data = {
            "name": "Team to be deleted",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)

        self.service.delete_object(instance)
        instance.refresh_from_db()

        self.assertFalse(instance.is_active)
