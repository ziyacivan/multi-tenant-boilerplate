from django.db import connection
from django.http.request import HttpRequest

from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomTenantMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        connection.set_schema_to_public()
        tenant_id = self.tenant_id_from_request(request)
        if not tenant_id:
            from django.http import HttpResponseNotFound

            return HttpResponseNotFound()

        domain_model = get_tenant_domain_model()
        try:
            tenant = self.get_tenant(domain_model, tenant_id)

            authentication_class = JWTAuthentication()
            header = authentication_class.get_header(request)
            if header:
                raw_token = authentication_class.get_raw_token(header)
                validated_token = authentication_class.get_validated_token(raw_token)
                user = authentication_class.get_user(validated_token)

                if tenant in user.tenants.all():
                    tenant.domain_url = self.hostname_from_request(request)
                    request.tenant = tenant
                    connection.set_tenant(request.tenant)
                    self.setup_url_routing(request)
                else:
                    return self.return_default_tenant(request)
        except domain_model.DoesNotExist:
            return self.return_default_tenant(request)

    @staticmethod
    def tenant_id_from_request(request: HttpRequest):
        return request.META.get("HTTP_X_CLIENT")

    def get_tenant(self, domain_model, tenant_id):
        domain = domain_model.objects.select_related("tenant").get(tenant__pk=tenant_id)
        return domain.tenant

    def return_default_tenant(self, request):
        default_tenant = self.no_tenant_found(
            request,
            self.hostname_from_request(request),
        )
        return default_tenant
