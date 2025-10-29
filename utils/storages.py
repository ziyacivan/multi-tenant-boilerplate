import os

from django.core.files.storage import FileSystemStorage

from django_tenants.utils import get_tenant_model, schema_context


class TenantFileSystemStorage(FileSystemStorage):
    """
    Tenant-aware file storage.

    Each tenant's files are stored in separate directories based on schema_name.
    Example: /mediafiles/evilcorp/profile_photos/image.jpg
    """

    def __init__(self, *args, **kwargs):
        from django.conf import settings

        kwargs["location"] = settings.MEDIA_ROOT
        super().__init__(*args, **kwargs)

    def get_tenant_path(self, name):
        """
        Returns tenant-specific file path.

        Args:
            name (str): Original file name

        Returns:
            str: Tenant-specific file path
        """
        from django_tenants.utils import get_tenant

        try:
            tenant = get_tenant()
            if tenant and tenant.schema_name != "public":
                return os.path.join(tenant.schema_name, name)
        except Exception:
            pass
        return name

    def path(self, name):
        """Returns full file path."""
        return super().path(self.get_tenant_path(name))

    def url(self, name):
        """Returns file URL."""
        return super().url(self.get_tenant_path(name))

    def save(self, name, content, max_length=None):
        """Saves file in tenant-specific directory."""
        tenant_path = self.get_tenant_path(name)
        return super().save(tenant_path, content, max_length)

    def delete(self, name):
        """Deletes file from tenant-specific directory."""
        tenant_path = self.get_tenant_path(name)
        return super().delete(tenant_path)

    def exists(self, name):
        """Checks if file exists in tenant-specific directory."""
        tenant_path = self.get_tenant_path(name)
        return super().exists(tenant_path)
