# from django.urls import reverse

# from django_tenants.test.cases import TenantTestCase
# from model_bakery import baker
# from rest_framework import status

# from employees.choices import EmployeeRole
# from employees.models import Employee
# from users.models import User
# from utils.tests.mixins import AuthenticatedTenantTestMixin


# class EmployeeViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
#     """
#     run: python manage.py test --keepdb employees.tests.test_views.EmployeeViewSetTestCase
#     """

#     @classmethod
#     def get_test_tenant_domain(cls):
#         return "test.localhost"

#     @classmethod
#     def get_test_schema_name(cls):
#         return "test"

#     def setUp(self):
#         super().setUp()
#         self.list_url = reverse("employee-list")

#     def test_list_success(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         for i in range(5):
#             user = self.create_test_user(email=f"employee{i}@test.com")
#             self.create_test_employee(user=user, first_name=f"Employee{i}")

#         response = self.get(self.list_url)

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("results", response.data)
#         self.assertEqual(response.data["count"], 6)

#     def test_list_with_pagination(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         for i in range(25):
#             user = self.create_test_user(email=f"employee{i}@test.com")
#             self.create_test_employee(user=user, first_name=f"Employee{i}")

#         response = self.get(self.list_url)

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data["results"]), 20)
#         self.assertIsNotNone(response.data["next"])

#     def test_list_ordering(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         user1 = self.create_test_user(email="first@test.com")
#         emp1 = self.create_test_employee(user=user1, first_name="First")

#         user2 = self.create_test_user(email="second@test.com")
#         emp2 = self.create_test_employee(user=user2, first_name="Second")

#         response = self.get(self.list_url)

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["results"][0]["id"], emp2.id)

#     def test_list_without_authentication(self):
#         self._auth_token = None

#         response = self.client.get(self.list_url)

#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_create_as_manager_success(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         new_user = self.create_test_user(email="newemployee@test.com")
#         data = {
#             "user": new_user.id,
#             "first_name": "New",
#             "last_name": "Employee",
#             "role": EmployeeRole.employee,
#         }

#         response = self.post(self.list_url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data["first_name"], "New")
#         self.assertEqual(response.data["last_name"], "Employee")
#         self.assertEqual(Employee.objects.count(), 2)

#     def test_create_as_owner_success(self):
#         self.authenticate_client(role=EmployeeRole.owner)

#         new_user = self.create_test_user(email="newemployee@test.com")
#         data = {
#             "user": new_user.id,
#             "first_name": "New",
#             "last_name": "Employee",
#             "role": EmployeeRole.employee,
#         }

#         response = self.post(self.list_url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Employee.objects.count(), 2)

#     def test_create_as_regular_employee_forbidden(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         new_user = self.create_test_user(email="newemployee@test.com")
#         data = {
#             "user": new_user.id,
#             "first_name": "New",
#             "last_name": "Employee",
#             "role": EmployeeRole.employee,
#         }

#         response = self.post(self.list_url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(Employee.objects.count(), 1)

#     def test_create_without_authentication(self):
#         new_user = self.create_test_user(email="newemployee@test.com")
#         data = {
#             "user": new_user.id,
#             "first_name": "New",
#             "last_name": "Employee",
#         }

#         response = self.client.post(
#             self.list_url, data, content_type="application/json"
#         )

#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_create_with_missing_required_fields(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         new_user = self.create_test_user(email="newemployee@test.com")
#         data = {
#             "user": new_user.id,
#         }

#         response = self.post(self.list_url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("first_name", response.data)
#         self.assertIn("last_name", response.data)

#     def test_create_with_invalid_data(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         data = {
#             "user": 99999,
#             "first_name": "New",
#             "last_name": "Employee",
#         }

#         response = self.post(self.list_url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_retrieve_success(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         url = reverse("employee-detail", kwargs={"pk": self.test_employee.id})
#         response = self.get(url)

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["id"], self.test_employee.id)
#         self.assertEqual(response.data["first_name"], self.test_employee.first_name)

#     def test_retrieve_without_authentication(self):
#         self.authenticate_client(role=EmployeeRole.employee)
#         employee_id = self.test_employee.id

#         self._auth_token = None

#         url = reverse("employee-detail", kwargs={"pk": employee_id})
#         response = self.client.get(url)

#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_retrieve_nonexistent_employee(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         url = reverse("employee-detail", kwargs={"pk": 99999})
#         response = self.get(url)

#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

#     def test_update_as_manager_success(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="Original", last_name="Name"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         data = {
#             "user": target_employee.user.id,
#             "first_name": "Updated",
#             "last_name": "Name",
#             "role": EmployeeRole.employee,
#         }

#         response = self.put(url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["first_name"], "Updated")

#         target_employee.refresh_from_db()
#         self.assertEqual(target_employee.first_name, "Updated")

#     def test_update_as_owner_success(self):
#         self.authenticate_client(role=EmployeeRole.owner)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="Original", last_name="Name"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         data = {
#             "user": target_employee.user.id,
#             "first_name": "Updated",
#             "last_name": "Name",
#             "role": EmployeeRole.employee,
#         }

#         response = self.put(url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["first_name"], "Updated")

#     def test_update_as_regular_employee_forbidden(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="Original", last_name="Name"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         data = {
#             "user": target_employee.user.id,
#             "first_name": "Updated",
#             "last_name": "Name",
#         }

#         response = self.put(url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

#     def test_partial_update_patch(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="Original", last_name="Name"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         data = {
#             "first_name": "Patched",
#         }

#         response = self.patch(url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["first_name"], "Patched")
#         self.assertEqual(response.data["last_name"], "Name")

#     def test_update_is_active_field_ignored(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="Original", last_name="Name"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         data = {
#             "user": target_employee.user.id,
#             "first_name": "Updated",
#             "last_name": "Name",
#             "is_active": False,
#             "role": EmployeeRole.employee,
#         }

#         response = self.put(url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#         target_employee.refresh_from_db()
#         self.assertTrue(target_employee.is_active)

#     def test_update_without_authentication(self):
#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="Original", last_name="Name"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         data = {
#             "first_name": "Updated",
#         }

#         response = self.client.patch(url, data, content_type="application/json")

#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_soft_delete_as_manager(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="ToDelete", last_name="Employee"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         response = self.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

#         target_employee.refresh_from_db()
#         target_user.refresh_from_db()

#         self.assertFalse(target_employee.is_active)
#         self.assertFalse(target_user.is_active)
#         self.assertTrue(Employee.objects.filter(id=target_employee.id).exists())

#     def test_hard_delete_as_manager(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="ToDelete", last_name="Employee"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         employee_id = target_employee.id
#         user_id = target_user.id

#         response = self.delete(f"{url}?force=true")

#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

#         self.assertFalse(Employee.objects.filter(id=employee_id).exists())
#         self.assertFalse(User.objects.filter(id=user_id).exists())

#     def test_delete_as_regular_employee_forbidden(self):
#         self.authenticate_client(role=EmployeeRole.employee)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="ToDelete", last_name="Employee"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         response = self.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

#         target_employee.refresh_from_db()
#         self.assertTrue(target_employee.is_active)

#     def test_delete_without_authentication(self):
#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="ToDelete", last_name="Employee"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         response = self.client.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_cannot_delete_owner_role(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="ToDelete", last_name="Employee"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         target_employee.role = EmployeeRole.owner
#         target_employee.save()

#         response = self.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         target_employee.refresh_from_db()
#         self.assertTrue(target_employee.is_active)

#     def test_cannot_hard_delete_owner_role(self):
#         self.authenticate_client(role=EmployeeRole.manager)

#         target_user = self.create_test_user(email="target@test.com")
#         target_employee = self.create_test_employee(
#             user=target_user, first_name="ToDelete", last_name="Employee"
#         )
#         url = reverse("employee-detail", kwargs={"pk": target_employee.id})

#         target_employee.role = EmployeeRole.owner
#         target_employee.save()

#         employee_id = target_employee.id

#         response = self.delete(f"{url}?force=true")

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertTrue(Employee.objects.filter(id=employee_id).exists())
