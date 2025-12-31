# Setup Guide

## Creating the Public Tenant (System Tenant)

The main project needs to be recognized as a tenant to start the process. Follow these steps:

```python
from tenant_users.tenants.utils import create_public_tenant

create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")
```

This command will create the public tenant and public domain in the public schema.

**Note:** The public tenant is used for:
- User registration and authentication
- Company creation requests
- System-wide operations that don't belong to a specific tenant

## Creating a Customer Tenant

### Step 1: Create a Super User

First, create a super user for the customer:

```python
from users.models import User

user = User.objects.create_user(
    email="user@evilcorp.com", 
    password="password", 
    is_staff=True
)
```

### Step 2: Create the Tenant

After creating the user, create the tenant record:

```python
from tenant_users.tenants.tasks import provision_tenant
from users.models import User

provision_tenant_owner = User.objects.get(email="user@evilcorp.com")

tenant, domain = provision_tenant(
    "EvilCorp", 
    "evilcorp", 
    provision_tenant_owner
)
```

**What happens:**
- Schema is automatically created (`evilcorp`)
- Migrations are automatically applied to the tenant schema
- Domain is created (`evilcorp.localhost` in development)
- Owner is linked to the tenant with staff and superuser permissions

### Alternative: Using ClientService

You can also use the `ClientService` for more control:

```python
from tenants.services import ClientService
from users.models import User

owner = User.objects.get(email="user@evilcorp.com")
service = ClientService()

tenant = service.create_object(
    name="Evil Corp",
    description="A fictional company",
    slug="evilcorp",
    owner=owner,
    legal_name="Evil Corporation Inc.",
    tax_no="1234567890",
    tax_office="Istanbul Tax Office",
    address="123 Main St, Istanbul",
    city="Istanbul",
    country="Turkey"
)
```

## Deleting a Customer Tenant

### Soft Delete (Recommended)

Soft delete deactivates the tenant without dropping the schema:

```python
from tenants.models import Client
from tenants.services import ClientService

evil = Client.objects.get(schema_name="evilcorp")
service = ClientService()
service.delete_object(evil)

# Result:
# - tenant.is_active = False
# - tenant.domain_url = "{timestamp}-{owner_id}-evilcorp.localhost"
# - All tenant users is_active = False
# - Schema is preserved (auto_drop_schema=False)
```

### Hard Delete (Drops Schema)

**Warning:** This will permanently delete the schema and all data:

```python
from tenants.models import Client

evil = Client.objects.get(schema_name="evilcorp")
evil.delete_tenant()  # Drops the schema permanently
```

## Deleting Tenant Users

### Deleting a User from a Tenant

```python
from users.models import User

user = User.objects.get(email="user@domain.com")
User.objects.delete_user(user)
```

### Deleting a User Without Tenant Connection

```python
from users.models import User

user = User.objects.get(email="user@domain.com")
user.delete(force_drop=True)
```

## Adding a User to a Tenant

```python
from tenants.models import Client
from users.models import User

user = User.objects.get(email="user@domain.com")
evil = Client.objects.get(schema_name="evilcorp")
evil.add_user(user)

# Optional: Set tenant-specific permissions
evil.add_user(user, is_staff=True, is_superuser=False)
```

## Operations Within Tenant Schema

All tenant-aware operations must be performed within `tenant_context()`:

```python
from django_tenants.utils import tenant_context
from tenants.models import Client
from users.models import User

# 1. Get the tenant object
tenant = Client.objects.get(schema_name="evilcorp")

# 2. Use tenant_context with the tenant object
with tenant_context(tenant):
    print(f"Switched to '{tenant.schema_name}' schema.")
    
    # All ORM queries within this block run in the tenant's schema
    from employees.models import Employee
    employees = Employee.objects.all()
    
    # Update tenant-specific user permissions
    user = User.objects.get(email="user@evilcorp.com")
    user.tenant_perms.is_staff = True
    user.tenant_perms.is_superuser = True
    user.tenant_perms.save()
    
    print(f"Updated permissions for user '{user.email}'.")
```

### Alternative: Using schema_context

You can also use `schema_context` with the schema name:

```python
from django_tenants.utils import schema_context

with schema_context("evilcorp"):
    from employees.models import Employee
    employees = Employee.objects.all()
```

## Reactivating a Deactivated Tenant

```python
from tenants.models import Client
from tenants.services import ClientService

tenant = Client.objects.get(schema_name="evilcorp")
service = ClientService()
service.active_client(tenant)

# Result:
# - tenant.is_active = True
# - tenant.domain_url = "evilcorp.localhost" (timestamp removed)
# - All tenant users is_active = True
```

## Common Operations

### Listing All Tenants

```python
from tenants.models import Client

all_tenants = Client.objects.all()
active_tenants = Client.objects.filter(is_active=True)
```

### Getting Tenant by Domain

```python
from tenants.models import Domain

domain = Domain.objects.get(domain="evilcorp.localhost")
tenant = domain.tenant
```

### Checking User's Tenants

```python
from users.models import User

user = User.objects.get(email="user@example.com")
user_tenants = user.tenants.all()

for tenant in user_tenants:
    print(f"User belongs to: {tenant.name} ({tenant.schema_name})")
```

## Best Practices

1. **Always use tenant_context:** Never access tenant models outside of tenant context
2. **Use soft delete:** Prefer `delete_object()` over `delete_tenant()` to preserve data
3. **Check tenant existence:** Always verify tenant exists before operations
4. **Handle errors:** Wrap tenant operations in try-except blocks
5. **Use services:** Prefer service layer methods over direct ORM operations

## Troubleshooting

### Schema Not Found Error

**Problem:** `DoesNotExist` error when accessing tenant models

**Solution:** Ensure you're within tenant context:

```python
# ❌ WRONG
employees = Employee.objects.all()  # DoesNotExist

# ✅ CORRECT
with tenant_context(tenant):
    employees = Employee.objects.all()
```

### User Not Found in Tenant

**Problem:** User exists but can't access tenant resources

**Solution:** Verify user is added to tenant:

```python
tenant = Client.objects.get(schema_name="evilcorp")
if user not in tenant.user_set.all():
    tenant.add_user(user)
```
