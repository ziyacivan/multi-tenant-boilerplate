# Company Creation Flow

## Overview

This document describes the complete flow for creating a new company (tenant) in the HRM API system.

## Prerequisites

1. **User Role:** A user must have the `owner` role to create a company.
2. **No Existing Company:** The user must not already be associated with another company.
   - This identifies the user as a new user who wants to create their own company.
3. **Public Schema Request:** The company creation request must be sent from the public schema (main application).

## Flow Steps

### 1. User Registration/Authentication

The user must first be registered in the public schema:

```python
from users.models import User

# User registration happens in public schema
user = User.objects.create_user(
    email="owner@company.com",
    password="secure_password"
)
```

### 2. Company Creation Request

The user sends a company creation request to the public schema API endpoint:

**Endpoint:** `POST /api/tenants/` (or equivalent public tenant endpoint)

**Request Schema:**
- The request must be sent from the public schema domain (e.g., `hrmore.com` or `localhost:8000`)
- The authenticated user must have `owner` role
- The user must not already have a company

**Request Body Example:**
```json
{
  "name": "Evil Corp",
  "description": "A fictional company",
  "slug": "evilcorp",
  "legal_name": "Evil Corporation Inc.",
  "tax_no": "1234567890",
  "tax_office": "Istanbul Tax Office",
  "address": "123 Main St, Istanbul",
  "invoice_address": "123 Main St, Istanbul",
  "city": "Istanbul",
  "country": "Turkey",
  "invoice_email_address": "billing@evilcorp.com",
  "short_name": "EvilCorp"
}
```

### 3. Backend Processing

The backend processes the request using `ClientService.create_object()`:

```python
from tenants.services import ClientService
from employees.choices import EmployeeRole

service = ClientService()

tenant = service.create_object(
    name="Evil Corp",
    description="A fictional company",
    slug="evilcorp",
    owner=request.user,  # Authenticated user
    legal_name="Evil Corporation Inc.",
    tax_no="1234567890",
    # ... other fields
)
```

**What happens during creation:**

1. **Validation:**
   - Checks if a company with the same slug already exists
   - Verifies the user doesn't already have a company (`owner.tenants.count() > 1`)
   - Raises `CompanyAlreadyExistsException` or `UserAlreadyHaveCompanyException` if validation fails

2. **Tenant Creation:**
   - Creates `Client` object with `schema_name` = slug
   - Creates `Domain` object with domain = slug (e.g., `evilcorp.localhost`)
   - Saves tenant and domain

3. **User Association:**
   - Links owner to tenant: `tenant.add_user(owner, is_superuser=True, is_staff=True)`

4. **Employee Creation:**
   - Switches to tenant schema context
   - Creates `Employee` record for the owner with `role=EmployeeRole.owner`
   - This happens in the tenant's schema, not the public schema

### 4. Response

The API returns the created tenant information:

```json
{
  "id": 1,
  "name": "Evil Corp",
  "slug": "evilcorp",
  "schema_name": "evilcorp",
  "description": "A fictional company",
  "is_active": true,
  "created_on": "2025-01-01T00:00:00Z",
  "updated_on": "2025-01-01T00:00:00Z"
}
```

## Request Schema Details

### Why Public Schema?

1. **User Storage:** All users are actually users in the main application. Therefore, every user has a record in the `public` schema.

2. **Company Creation Endpoint:** The user must send the company creation request from within the main application, for example: `hrmore.com` or `localhost:8000` (not from a tenant-specific domain).

3. **Authentication:** The user authenticates against the public schema, and the system uses this authenticated user as the company owner.

### Example Request Flow

```
1. User registers at: http://hrmore.com/api/auth/register/
2. User logs in at: http://hrmore.com/api/auth/login/
3. User creates company at: http://hrmore.com/api/tenants/
   - Request includes JWT token
   - Backend validates user is owner and has no existing company
   - Backend creates tenant and switches to tenant schema
   - Backend creates employee record in tenant schema
4. User can now access tenant at: http://evilcorp.hrmore.com/
```

## Post-Creation Operations

### Fixing Tenant Permissions Synchronization

If there's a problem with the user's permissions in the company schema (synchronization issue), you can fix it using the implementation described in the [Setup Guide](./setup.md#operations-within-tenant-schema):

```python
from django_tenants.utils import tenant_context
from tenants.models import Client
from users.models import User

tenant = Client.objects.get(schema_name="evilcorp")
user = User.objects.get(email="owner@company.com")

with tenant_context(tenant):
    user.tenant_perms.is_staff = True
    user.tenant_perms.is_superuser = True
    user.tenant_perms.save()
    
    print(f"Updated permissions for user '{user.email}'.")
```

## Error Handling

### CompanyAlreadyExistsException

**Triggered when:** A company with the same slug already exists.

**Solution:** Use a different slug for the company.

### UserAlreadyHaveCompanyException

**Triggered when:** The user already has a company associated.

**Solution:** 
- Use a different user account
- Or delete the existing company first (if appropriate)

## API Endpoint Details

### Create Company Endpoint

**URL:** `POST /api/tenants/`

**Authentication:** Required (JWT Token)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "slug": "string (required, unique)",
  "legal_name": "string (optional)",
  "tax_no": "string (optional)",
  "tax_office": "string (optional)",
  "address": "string (optional)",
  "invoice_address": "string (optional)",
  "city": "string (optional)",
  "country": "string (optional)",
  "invoice_email_address": "email (optional)",
  "short_name": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Evil Corp",
  "slug": "evilcorp",
  "schema_name": "evilcorp",
  "description": "A fictional company",
  "is_active": true,
  "created_on": "2025-01-01T00:00:00Z",
  "updated_on": "2025-01-01T00:00:00Z"
}
```

**Error Responses:**

- **400 Bad Request:** Validation errors
- **401 Unauthorized:** Missing or invalid authentication
- **403 Forbidden:** User doesn't have owner role or already has a company
- **409 Conflict:** Company with slug already exists

## Testing the Flow

### Manual Testing

```python
# 1. Create user in public schema
from users.models import User

user = User.objects.create_user(
    email="test@example.com",
    password="testpass123",
    is_staff=True
)

# 2. Create company via service
from tenants.services import ClientService

service = ClientService()
tenant = service.create_object(
    name="Test Company",
    description="Test description",
    slug="testcompany",
    owner=user
)

# 3. Verify tenant was created
assert tenant.schema_name == "testcompany"
assert tenant.owner == user

# 4. Verify employee was created in tenant schema
from django_tenants.utils import tenant_context
from employees.models import Employee

with tenant_context(tenant):
    employee = Employee.objects.get(user=user)
    assert employee.role == EmployeeRole.owner
```

## Best Practices

1. **Validate slug uniqueness:** Always check slug availability before creation
2. **Handle errors gracefully:** Provide clear error messages to users
3. **Log operations:** Log all company creation attempts for audit purposes
4. **Verify user role:** Ensure user has owner role before allowing creation
5. **Check existing companies:** Prevent users from creating multiple companies
6. **Use service layer:** Always use `ClientService` instead of direct ORM operations

## Related Documentation

- [Setup Guide](./../setup.md)
- [Tenant Management](./../tenants.md)
- [Migration Guide](./../migrations.md)
