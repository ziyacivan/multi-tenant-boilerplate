from django.conf import settings
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
