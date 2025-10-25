from django_tenants.test.cases import TenantTestCase

from titles.services import TitleService
from utils.tests.mixins import TenantTestCaseMixin


class TitleServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb titles.tests.test_services.TitleServiceTestCase
    """

    service = TitleService()

    def test_create_object(self):
        data = {
            "name": "Test Title",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)
        self.assertEqual(instance.name, data["name"])

    def test_create_object_unique_constraint(self):
        data = {
            "name": "Unique Title",
        }
        instance1 = self.service.create_object(**data)
        self.assertIsNotNone(instance1)

        with self.assertRaises(Exception):
            self.service.create_object(**data)

    def test_update_object(self):
        data = {
            "name": "Initial Title",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)
        self.assertEqual(instance.name, data["name"])

        updated_data = {
            "name": "Updated Title",
        }
        updated_instance = self.service.update_object(instance, **updated_data)
        self.assertIsNotNone(updated_instance)
        self.assertEqual(updated_instance.name, updated_data["name"])

    def test_update_object_unique_constraint(self):
        data1 = {
            "name": "First Title",
        }
        instance1 = self.service.create_object(**data1)
        self.assertIsNotNone(instance1)

        data2 = {
            "name": "Second Title",
        }
        instance2 = self.service.create_object(**data2)
        self.assertIsNotNone(instance2)

        with self.assertRaises(Exception):
            self.service.update_object(instance2, name="First Title")

    def test_delete_object(self):
        data = {
            "name": "Title to be deleted",
        }
        instance = self.service.create_object(**data)
        self.assertIsNotNone(instance)

        self.service.delete_object(instance)
        instance.refresh_from_db()

        self.assertFalse(instance.is_active)
