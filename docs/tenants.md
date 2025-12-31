# Tenant Management Guide

## How is tenant management performed?

For our main application to be accessible, we need to create a main `Tenant` at the beginning:

```python
from tenants.models import Client, Domain

# Create your public tenant
tenant = Client(
    schema_name='public',
    name='HRM',
)
tenant.save()

# Add one or more domains for the tenant
domain = Domain()
domain.domain = 'my-domain.com'  # Don't add your port or www here! On a local server you'll want to use localhost here
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

**Note:** In practice, you should use `create_public_tenant()` utility function instead:

```python
from tenant_users.tenants.utils import create_public_tenant

create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")
```

## How is tenant management performed for a customer?

To introduce a customer to the system, follow these steps:

### Method 1: Using provision_tenant (Recommended)

```python
from tenant_users.tenants.tasks import provision_tenant
from users.models import User

# Create owner user first
owner = User.objects.create_user(
    email="owner@company.com",
    password="secure_password",
    is_staff=True
)

# Provision tenant
tenant, domain = provision_tenant(
    tenant_name="Company Name",
    tenant_slug="company",
    owner=owner
)
```

**What happens automatically:**
- Schema is created (`company`)
- Migrations are applied to the tenant schema
- Domain is created (`company.localhost` in development)
- Owner is linked with staff and superuser permissions

### Method 2: Using ClientService

```python
from tenants.services import ClientService
from users.models import User

owner = User.objects.get(email="owner@company.com")
service = ClientService()

tenant = service.create_object(
    name="Company Name",
    description="Company description",
    slug="company",
    owner=owner,
    legal_name="Company Legal Name Inc.",
    tax_no="1234567890",
    tax_office="Tax Office Name",
    address="123 Main St",
    city="Istanbul",
    country="Turkey"
)
```

### Method 3: Manual Creation

```python
from tenants.models import Client, Domain

# Create your first real tenant
tenant = Client(
    schema_name='tenant1',
    name='Fonzy Tenant',
    slug='tenant1'
)
tenant.save()  # migrate_schemas automatically called, your tenant is ready to be used!

# Add one or more domains for the tenant
domain = Domain()
domain.domain = 'tenant.my-domain.com'  # Don't add your port or www here!
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

## How is a superuser created for a customer's system?

### Using Django Management Command

```bash
python manage.py create_tenant_superuser --username=admin --schema=public
# or
python manage.py create_tenant_superuser --username=admin --schema=customer-schema-name
```

### Using Python Code

```python
from django_tenants.utils import tenant_context
from tenants.models import Client
from users.models import User

tenant = Client.objects.get(schema_name="company")
user = User.objects.get(email="admin@company.com")

with tenant_context(tenant):
    user.tenant_perms.is_staff = True
    user.tenant_perms.is_superuser = True
    user.tenant_perms.save()
```

## How is a customer removed from the system?

### Option 1: Soft Delete (Recommended)

Soft delete deactivates the tenant without dropping the schema:

```python
from tenants.models import Client
from tenants.services import ClientService

tenant = Client.objects.get(schema_name="company")
service = ClientService()
service.delete_object(tenant)

# Result:
# - tenant.is_active = False
# - tenant.domain_url = "{timestamp}-{owner_id}-company.localhost"
# - All tenant users is_active = False
# - Schema is preserved (data is not lost)
```

### Option 2: Hard Delete (Drops Schema)

**Warning:** This will permanently delete the schema and all data:

1. **Direct database connection:** Connect to the database remotely and drop the schema directly, but this will cause data loss.

2. **Using auto_drop_schema:** Set `auto_drop_schema = True` in the Client model and delete via Django ORM through a service, but this will also drop the schema and cause data loss.

```python
from tenants.models import Client

tenant = Client.objects.get(schema_name="company")
tenant.delete_tenant()  # Drops schema permanently
```

**Best Practice:** Always use soft delete unless you're certain you want to permanently remove all data.

## How does the Users module work?

The `users` module and the `User` records within it are included in the `TENANT_APPS` list in `config/settings.py`, which means:

- Each customer has their own `users` table
- Users are isolated from each other
- Users in different tenant schemas cannot see each other
- All users also exist in the public schema for authentication purposes

### User Isolation Example

```python
from django_tenants.utils import tenant_context
from tenants.models import Client
from users.models import User

# In public schema
all_users = User.objects.all()  # All users across all tenants

# In tenant schema
tenant = Client.objects.get(schema_name="company")
with tenant_context(tenant):
    tenant_users = User.objects.all()  # Only users in this tenant
```

## Tenant Context Operations

All operations on tenant-specific models must be performed within tenant context:

```python
from django_tenants.utils import tenant_context, schema_context
from tenants.models import Client
from employees.models import Employee

tenant = Client.objects.get(schema_name="company")

# Method 1: Using tenant_context
with tenant_context(tenant):
    employees = Employee.objects.all()
    print(f"Tenant: {tenant.name}, Employees: {employees.count()}")

# Method 2: Using schema_context
with schema_context("company"):
    employees = Employee.objects.all()
```

## Tenant Activation/Deactivation

### Deactivate Tenant

```python
from tenants.services import ClientService

service = ClientService()
service.delete_object(tenant)
```

### Reactivate Tenant

```python
from tenants.services import ClientService

service = ClientService()
service.active_client(tenant)
```

## Adding Users to Tenants

```python
from tenants.models import Client
from users.models import User

tenant = Client.objects.get(schema_name="company")
user = User.objects.get(email="employee@company.com")

# Add user to tenant
tenant.add_user(user)

# Add user with specific permissions
tenant.add_user(user, is_staff=True, is_superuser=False)
```

## Domain Management

### Adding a Domain to a Tenant

```python
from tenants.models import Client, Domain

tenant = Client.objects.get(schema_name="company")

domain = Domain()
domain.domain = "company.example.com"
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

### Changing Primary Domain

```python
from tenants.models import Domain

# Set new primary domain
new_primary = Domain.objects.get(domain="new-company.example.com")
new_primary.is_primary = True
new_primary.save()

# Unset old primary domain
old_primary = Domain.objects.get(domain="old-company.example.com")
old_primary.is_primary = False
old_primary.save()
```

## Best Practices

1. **Always use tenant context:** Never access tenant models outside of tenant context
2. **Use soft delete:** Prefer soft delete to preserve data for potential recovery
3. **Validate tenant existence:** Always check if tenant exists before operations
4. **Use service layer:** Prefer service methods over direct ORM operations
5. **Handle errors gracefully:** Wrap tenant operations in try-except blocks
6. **Document tenant operations:** Document all tenant-specific operations clearly

## Troubleshooting

### Tenant Not Found

**Problem:** `Client.DoesNotExist` error

**Solution:** Verify tenant exists and schema name is correct:

```python
try:
    tenant = Client.objects.get(schema_name="company")
except Client.DoesNotExist:
    print("Tenant not found")
```

### Schema Access Error

**Problem:** Cannot access tenant models

**Solution:** Ensure you're within tenant context:

```python
# ❌ WRONG
employees = Employee.objects.all()  # DoesNotExist

# ✅ CORRECT
with tenant_context(tenant):
    employees = Employee.objects.all()
```

### Domain Routing Issues

**Problem:** Requests not routing to correct tenant

**Solution:** 
1. Check domain configuration in database
2. Verify `is_primary` flag is set correctly
3. Check middleware configuration in `settings.py`
4. Verify domain matches request host header

