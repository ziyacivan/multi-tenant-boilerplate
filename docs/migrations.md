# Migration Management Guide

## Overview

In a multi-tenant Django application using django-tenants, migrations are handled differently than in a standard Django application. The system distinguishes between:

- **Shared apps:** Apps that exist in the public schema only (e.g., `tenants`, `users`)
- **Tenant apps:** Apps that exist in each tenant schema (e.g., `employees`, `titles`, `teams`)

## Migration Commands

### Shared Apps Migrations

If you make changes to shared apps (apps in `SHARED_APPS` in `settings.py`), run:

```bash
python manage.py migrate_schemas --shared
```

**Shared apps include:**
- `django_tenants`
- `tenants`
- `users`
- `django.contrib.contenttypes`
- `django.contrib.sessions`
- `django.contrib.messages`
- `django.contrib.staticfiles`
- `django.contrib.admin`
- `django.contrib.auth`
- `rest_framework`
- `rest_framework_simplejwt`
- `corsheaders`
- `drf_spectacular`
- `django_extensions`
- `tenant_users.permissions`
- `tenant_users.tenants`

**Example:**
```bash
# After modifying tenants/models.py
python manage.py makemigrations tenants
python manage.py migrate_schemas --shared
```

### Tenant Apps Migrations

If you make changes to tenant-specific apps (apps in `TENANT_APPS` in `settings.py`), run:

```bash
python manage.py migrate_schemas
```

**Tenant apps include:**
- `django.contrib.admin`
- `django.contrib.auth`
- `django.contrib.contenttypes`
- `django.contrib.messages`
- `django.contrib.staticfiles`
- `tenant_users.permissions`
- `employees`
- `titles`
- `teams`

**Example:**
```bash
# After modifying employees/models.py
python manage.py makemigrations employees
python manage.py migrate_schemas
```

**What happens:**
- Migrations are applied to all existing tenant schemas
- New tenants will automatically have these migrations applied when created

### Creating Migration Files

To create migration files, use the standard Django command:

```bash
# Create migrations for a specific app
python manage.py makemigrations <app_name>

# Create migrations for all apps
python manage.py makemigrations

# Dry run (check what would be created)
python manage.py makemigrations --dry-run
```

**Examples:**
```bash
python manage.py makemigrations employees
python manage.py makemigrations tenants
python manage.py makemigrations titles
```

## Migration Workflow

### Standard Workflow

1. **Make model changes** in your app's `models.py`
2. **Create migration file:**
   ```bash
   python manage.py makemigrations <app_name>
   ```
3. **Apply migrations:**
   - For shared apps: `python manage.py migrate_schemas --shared`
   - For tenant apps: `python manage.py migrate_schemas`
4. **Test the changes** in your development environment

### Development Workflow

```bash
# 1. Modify model
# Edit employees/models.py

# 2. Create migration
python manage.py makemigrations employees

# 3. Review migration file
# Check employees/migrations/XXXX_*.py

# 4. Apply to all tenant schemas
python manage.py migrate_schemas

# 5. Test
python manage.py test employees
```

### Production Workflow

```bash
# 1. Create migrations locally
python manage.py makemigrations <app_name>

# 2. Commit migration files
git add <app>/migrations/
git commit -m "Add migration for <app>"
git push

# 3. Deploy code

# 4. Apply migrations
python manage.py migrate_schemas --shared  # If shared app
python manage.py migrate_schemas            # If tenant app
```

## Docker Workflow

When using Docker, run migrations inside the container:

```bash
# Shared apps
docker-compose exec web python manage.py migrate_schemas --shared

# Tenant apps
docker-compose exec web python manage.py migrate_schemas

# Or using uv
docker-compose exec web uv run python manage.py migrate_schemas --shared
docker-compose exec web uv run python manage.py migrate_schemas
```

## Migration Best Practices

### 1. Always Review Migration Files

Before applying migrations, review the generated migration file:

```bash
python manage.py makemigrations <app_name>
# Review the generated file in <app>/migrations/
```

### 2. Test Migrations Locally First

Always test migrations in your development environment before deploying:

```bash
# Test on local database
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
```

### 3. Backup Before Production Migrations

Before applying migrations in production, backup your database:

```bash
# PostgreSQL backup
pg_dump -U hrm_user hrm_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Use Transactional Migrations

Django migrations are transactional by default. If a migration fails, it will rollback automatically.

### 5. Handle Data Migrations Carefully

For data migrations in tenant apps, ensure you're in the correct tenant context:

```python
# employees/migrations/0002_migrate_data.py
from django.db import migrations
from django_tenants.utils import schema_context

def migrate_employee_data(apps, schema_editor):
    Employee = apps.get_model('employees', 'Employee')
    # Get all tenant schemas
    from tenants.models import Client
    for tenant in Client.objects.all():
        with schema_context(tenant.schema_name):
            # Perform data migration
            Employee.objects.filter(...).update(...)

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(migrate_employee_data),
    ]
```

## Common Issues and Solutions

### Issue: Migration Applied to Wrong Schema

**Problem:** Migration applied to public schema instead of tenant schemas

**Solution:** 
- For tenant apps, use `migrate_schemas` (without `--shared`)
- For shared apps, use `migrate_schemas --shared`

### Issue: Migration Fails on Specific Tenant

**Problem:** Migration works on some tenants but fails on others

**Solution:**
1. Check tenant-specific data that might cause issues
2. Use `--schema` flag to test on specific tenant:
   ```bash
   python manage.py migrate_schemas --schema=tenant_name
   ```

### Issue: Migration File Conflicts

**Problem:** Multiple developers created migrations with same number

**Solution:**
1. Rename migration files to resolve conflicts
2. Update dependencies in migration files
3. Test thoroughly before committing

### Issue: Missing Migration Dependencies

**Problem:** Migration fails due to missing dependencies

**Solution:**
1. Check `dependencies` list in migration file
2. Ensure all required migrations are applied
3. Use `--fake` flag carefully if needed (not recommended)

## Checking Migration Status

### List Pending Migrations

```bash
# Check shared apps
python manage.py showmigrations --shared

# Check tenant apps
python manage.py showmigrations
```

### Check Specific Tenant

```bash
python manage.py showmigrations --schema=tenant_name
```

## Rolling Back Migrations

### Rollback Last Migration

```bash
# Shared apps
python manage.py migrate_schemas --shared <app_name> <previous_migration_number>

# Tenant apps
python manage.py migrate_schemas <app_name> <previous_migration_number>
```

**Example:**
```bash
# Rollback employees app to migration 0002
python manage.py migrate_schemas employees 0002
```

**Warning:** Rolling back migrations can cause data loss. Always backup before rolling back.

## Migration Files Location

Migration files are stored in each app's `migrations/` directory:

```
employees/
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py
│   ├── 0002_employee_attributes.py
│   └── ...
```

## Tips

1. **Keep migrations small:** Break large changes into multiple migrations
2. **Test with real data:** Test migrations with production-like data
3. **Document complex migrations:** Add comments for complex data migrations
4. **Don't edit applied migrations:** Never edit migrations that have been applied to production
5. **Use squashing for old migrations:** Consider squashing old migrations to reduce migration count

## Related Documentation

- [Django Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [django-tenants Migrations](https://django-tenants.readthedocs.io/en/latest/use.html#migrations)
- [Setup Guide](./setup.md)
- [Tenant Management](./tenants.md)

