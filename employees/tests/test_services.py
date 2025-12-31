from django_tenants.test.cases import TenantTestCase
from model_bakery import baker

from employees.choices import EmployeeGender, EmployeeRole
from employees.exceptions import CannotDeleteEmployeeException
from employees.models import Employee, PersonalDetail
from employees.serializers import EmployeeCreateSerializer
from employees.services import EmployeeService
from users.models import User
from utils.tests.mixins import TenantTestCaseMixin


class EmployeeServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb employees.tests.test_services.EmployeeServiceTestCase
    """

    service = EmployeeService()

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        self.user = baker.make(User, is_active=True)
        self.user.set_password("testpassword")
        self.user.save()

        self.employee = baker.make(
            Employee,
            user=self.user,
            first_name="John",
            last_name="Doe",
            role=EmployeeRole.employee,
            is_active=True,
        )

    def test_create_object_success(self):
        user = baker.make(User)
        employee = self.service.create_object(
            user=user,
            first_name="Jane",
            last_name="Doe",
            gender=EmployeeGender.female,
        )
        self.assertIsNotNone(employee)
        self.assertIsNotNone(employee)
        self.assertEqual(employee.user, user)
        self.assertEqual(employee.first_name, "Jane")
        self.assertEqual(Employee.objects.count(), 2)

    def test_create_object_with_optional_params(self):
        user = baker.make(User)
        employee = self.service.create_object(
            user=user,
            first_name="Sam",
            last_name="Smith",
            gender=EmployeeGender.male,
            role=EmployeeRole.manager,
        )
        self.assertIsNotNone(employee)
        self.assertEqual(employee.role, EmployeeRole.manager)

    def test_update_object_success(self):
        updated_employee = self.service.update_object(
            instance=self.employee, first_name="Johnathan", last_name="Doer"
        )
        self.employee.refresh_from_db()
        self.assertEqual(updated_employee.first_name, "Johnathan")
        self.assertEqual(self.employee.first_name, "Johnathan")
        self.assertEqual(self.employee.last_name, "Doer")

    def test_delete_object_soft_delete(self):
        self.assertTrue(self.employee.is_active)
        self.assertTrue(self.employee.user.is_active)

        self.service.delete_object(instance=self.employee, force_delete=False)

        self.employee.refresh_from_db()
        self.employee.user.refresh_from_db()

        self.assertFalse(self.employee.is_active)
        self.assertFalse(self.employee.user.is_active)

        self.assertTrue(Employee.objects.filter(id=self.employee.id).exists())
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_delete_object_force_delete(self):
        employee_id = self.employee.id
        user_id = self.user.id

        self.service.delete_object(instance=self.employee, force_delete=True)

        with self.assertRaises(Employee.DoesNotExist):
            Employee.objects.get(id=employee_id)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)

    def test_delete_object_owner_raises_exception(self):
        self.employee.role = EmployeeRole.owner
        self.employee.save()

        with self.assertRaises(CannotDeleteEmployeeException):
            self.service.delete_object(instance=self.employee, force_delete=False)

        with self.assertRaises(CannotDeleteEmployeeException):
            self.service.delete_object(instance=self.employee, force_delete=True)

        self.employee.refresh_from_db()
        self.assertTrue(self.employee.is_active)

        self.assertTrue(Employee.objects.filter(id=self.employee.id).exists())

    def test_create_object_without_user(self):
        serializer = EmployeeCreateSerializer(
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "test@test.com",
            }
        )
        serializer.is_valid(raise_exception=True)
        employee = self.service.create_object(**serializer.validated_data)
        self.assertIsNotNone(employee)

    def test_get_personal_detail(self):
        self.employee.personaldetail = baker.make(
            PersonalDetail,
            employee=self.employee,
            personal_phone="1234567890",
        )
        self.employee.personaldetail.save()
        personal_detail = self.service.get_personal_detail(self.employee)
        self.assertIsNotNone(personal_detail)
        self.assertEqual(personal_detail.personal_phone, "1234567890")

    def test_get_personal_detail_none(self):
        personal_detail = self.service.get_personal_detail(self.employee)
        self.assertIsNone(personal_detail)

    def test_create_or_update_personal_detail(self):
        personal_detail: PersonalDetail | None = (
            self.service.create_or_update_personal_detail(
                employee=self.employee,
                personal_phone="0987654321",
                address="123 Main St",
            )
        )
        self.assertIsNotNone(personal_detail)
        self.assertEqual(personal_detail.personal_phone, "0987654321")
        self.assertEqual(personal_detail.address, "123 Main St")

        updated_personal_detail: PersonalDetail | None = (
            self.service.create_or_update_personal_detail(
                employee=self.employee,
                personal_phone="1112223333",
            )
        )
        self.assertIsNotNone(updated_personal_detail)
        self.assertEqual(updated_personal_detail.personal_phone, "1112223333")
        self.assertEqual(updated_personal_detail.address, "123 Main St")
