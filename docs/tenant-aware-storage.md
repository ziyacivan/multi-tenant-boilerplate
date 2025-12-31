# 📁 Tenant-Aware Storage

## Overview

We have implemented a **tenant-aware storage** structure where each company's files are kept in a separate folder. This ensures that any company (e.g., EvilCorp) cannot see the images or documents of another company (e.g., AcmeCorp).

## Directory Structure

```
mediafiles/
├── evilcorp/              ← All files for EvilCorp
│   └── employees/photos/
│       └── photo_123.jpg
├── acmecorp/              ← All files for AcmeCorp
│   └── employees/photos/
│       └── photo_456.jpg
├── public/                ← Files for public schema (if any)
└── ...
```

## How It Works

### Implementation

The tenant-aware storage is implemented using a custom storage class:

```python
# utils/storages.py
from django.core.files.storage import FileSystemStorage
from django.db import connection

class TenantFileSystemStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        if location is None:
            location = settings.MEDIA_ROOT
        super().__init__(location, base_url)

    def _save(self, name, content):
        # The tenant is set on the connection by the CustomTenantMiddleware
        tenant = connection.tenant
        if tenant:
            name = f"{tenant.schema_name}/{name}"
        return super()._save(name, content)
```

### Usage in Models

The storage is used in model fields that need tenant isolation:

```python
# employees/models.py
from utils.storages import TenantFileSystemStorage

class Employee(BaseModel):
    photo = models.ImageField(
        _("photo"),
        upload_to="employees/photos/",
        storage=TenantFileSystemStorage(),
        null=True,
        blank=True,
    )
```

### Settings Configuration

The default file storage is configured in `settings.py`:

```python
# config/settings.py
DEFAULT_FILE_STORAGE = "utils.storages.TenantFileSystemStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"
```

## API Usage

### No API Changes Required

**The API has not changed.** To upload an employee profile photo, you still use the `PATCH /api/employees/{id}/` endpoint with `multipart/form-data`:

**Request Example:**
```bash
curl -X PATCH \
  https://evilcorp.localhost:8000/api/employees/1/ \
  -H "Authorization: Bearer <token>" \
  -F "photo=@/path/to/photo.jpg"
```

### Automatic Tenant Detection

When a request is made through a tenant domain (e.g., `https://evilcorp.localhost:8000`), the file is automatically saved to the correct folder:

1. **Middleware Detection:** `CustomTenantMiddleware` identifies the tenant from the domain
2. **Connection Setting:** The tenant is set on the database connection
3. **Storage Routing:** `TenantFileSystemStorage._save()` prepends the tenant's schema name to the file path
4. **File Storage:** File is saved to `mediafiles/evilcorp/employees/photos/photo_123.jpg`

### Response URL

The `photo` field in the response now includes the tenant name in the URL:

```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "photo": "https://evilcorp.localhost:8000/media/evilcorp/employees/photos/photo_123.jpg"
}
```

## Security Benefits

### Data Isolation

1. **File Separation:** Each tenant's files are physically separated in different directories
2. **URL Protection:** Files can only be accessed through the tenant's domain
3. **No Cross-Tenant Access:** Even if a user knows another tenant's file path, they cannot access it through their own tenant domain

### Example Scenario

```
Tenant A (evilcorp):
- Files stored at: mediafiles/evilcorp/employees/photos/photo_123.jpg
- Accessible at: https://evilcorp.localhost:8000/media/evilcorp/employees/photos/photo_123.jpg

Tenant B (acmecorp):
- Files stored at: mediafiles/acmecorp/employees/photos/photo_456.jpg
- Accessible at: https://acmecorp.localhost:8000/media/acmecorp/employees/photos/photo_456.jpg

Even if Tenant A user tries to access:
https://evilcorp.localhost:8000/media/acmecorp/employees/photos/photo_456.jpg
→ File not found (404) because the file doesn't exist in evilcorp's directory
```

## Implementation Details

### Middleware Integration

The `CustomTenantMiddleware` sets the tenant on the database connection:

```python
# tenants/middleware.py
from django_tenants.middleware import TenantMainMiddleware

class CustomTenantMiddleware(TenantMainMiddleware):
    # Sets connection.tenant based on the request domain
    pass
```

### Storage Class Behavior

1. **File Save:** When `_save()` is called, it checks `connection.tenant`
2. **Path Prefixing:** If tenant exists, prepends `{tenant.schema_name}/` to the file path
3. **Public Schema:** If no tenant (public schema), files are saved without prefix (or to `public/` folder if needed)

### File Retrieval

When retrieving files:
- Django's `FileField.url` property automatically generates the correct URL
- The URL includes the tenant schema name in the path
- Static file serving handles the request based on the tenant domain

## Usage Examples

### Uploading a File

```python
# In a view or service
from employees.models import Employee

employee = Employee.objects.get(id=1)
employee.photo = request.FILES['photo']
employee.save()

# File is automatically saved to:
# mediafiles/{tenant_schema_name}/employees/photos/{filename}
```

### Accessing File URL

```python
# In a serializer or view
employee = Employee.objects.get(id=1)
photo_url = employee.photo.url

# Returns: /media/evilcorp/employees/photos/photo_123.jpg
# Full URL: https://evilcorp.localhost:8000/media/evilcorp/employees/photos/photo_123.jpg
```

### Checking File Existence

```python
employee = Employee.objects.get(id=1)
if employee.photo:
    print(f"Photo exists: {employee.photo.path}")
    print(f"Photo URL: {employee.photo.url}")
```

## Best Practices

1. **Always use TenantFileSystemStorage:** Use this storage for all file fields that need tenant isolation
2. **Test file uploads:** Test file uploads from different tenant domains
3. **Monitor disk usage:** Each tenant's files are separate, so monitor disk usage per tenant
4. **Backup strategy:** Include tenant-specific media files in backup strategies
5. **File cleanup:** Implement cleanup for deleted files to save disk space

## Troubleshooting

### File Not Found (404)

**Problem:** File returns 404 even though it exists

**Solutions:**
1. Check that the request is made through the correct tenant domain
2. Verify the file path includes the tenant schema name
3. Check file permissions on the server
4. Verify `MEDIA_ROOT` and `MEDIA_URL` settings

### Wrong Tenant Folder

**Problem:** File saved to wrong tenant folder

**Solutions:**
1. Check that `CustomTenantMiddleware` is properly configured
2. Verify the request domain matches the tenant
3. Check that `connection.tenant` is set correctly in middleware

### Public Schema Files

**Problem:** Need to handle files in public schema

**Solution:** The storage class handles this automatically. If `connection.tenant` is `None`, files are saved without the tenant prefix (or you can modify to save to `public/` folder).

## Migration Notes

If you're migrating from non-tenant-aware storage:

1. **Existing Files:** Move existing files to tenant-specific folders manually
2. **Database:** Update file paths in the database to include tenant schema name
3. **URLs:** Update any hardcoded file URLs to use the new format

## Related Documentation

- [Setup Guide](./setup.md)
- [Tenant Management](./tenants.md)
- [Docker Guide](./docker.md)
