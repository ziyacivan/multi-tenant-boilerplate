import os

from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context
from tenant_users.tenants.tasks import provision_tenant
from tenant_users.tenants.utils import create_public_tenant

from tenants.models import Client, Domain
from users.models import User


class Command(BaseCommand):
    help = "Creates development tenants"

    def handle(self, *args, **options):
        dev_auto_setup = os.getenv("DEV_AUTO_SETUP", "true").lower() == "true"

        if not dev_auto_setup:
            self.stdout.write(
                self.style.WARNING("DEV_AUTO_SETUP=false, skipping setup")
            )
            return

        self.stdout.write(self.style.WARNING("=== Development Tenant Setup ===\n"))

        public_domain = os.getenv("DEV_PUBLIC_DOMAIN", "localhost")
        public_owner = os.getenv("DEV_PUBLIC_OWNER", "admin@localhost.com")

        try:
            public_tenant = Client.objects.get(schema_name="public")
            self.stdout.write(self.style.SUCCESS("✓ Public tenant is already created"))
        except Client.DoesNotExist:
            self.stdout.write("Public tenant is being created...")
            try:
                create_public_tenant(domain_url=public_domain, owner_email=public_owner)
                self.stdout.write(self.style.SUCCESS("✓ Public tenant created"))
                self.stdout.write(f"  Domain: {public_domain}")
                self.stdout.write(f"  Owner: {public_owner}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Public tenant creation failed: {e}")
                )
                return

        create_demo = os.getenv("DEV_DEMO_TENANT", "true").lower() == "true"

        if create_demo:
            demo_name = os.getenv("DEV_DEMO_NAME", "Demo Company")
            demo_slug = os.getenv("DEV_DEMO_SLUG", "demo")
            demo_owner_email = os.getenv("DEV_DEMO_OWNER", "demo@demo.local")
            demo_password = os.getenv("DEV_DEMO_PASSWORD", "demo123")

            try:
                demo_tenant = Client.objects.get(schema_name=demo_slug)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {demo_name} tenant already created")
                )
            except Client.DoesNotExist:
                self.stdout.write(f"\n{demo_name} tenant is being created...")
                try:
                    # Demo owner kullanıcısı
                    demo_owner = None
                    try:
                        demo_owner = User.objects.get(email=demo_owner_email)
                        self.stdout.write("  Owner user already exists")
                    except User.DoesNotExist:
                        demo_owner = User.objects.create_user(
                            email=demo_owner_email,
                            password=demo_password,
                            is_staff=True,
                        )
                        self.stdout.write("  Owner user created")

                    # Tenant provision
                    tenant, domain = provision_tenant(
                        demo_name,  # tenant_name
                        demo_slug,  # tenant_slug
                        demo_owner,  # user (positional argument)
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {demo_name} tenant created")
                    )
                    self.stdout.write(f"  Name: {tenant.name}")
                    self.stdout.write(f"  Schema: {tenant.schema_name}")
                    self.stdout.write(f"  Domain: {domain.domain}")
                    self.stdout.write(f"  Owner: {demo_owner.email} / {demo_password}")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ {demo_name} tenant creation failed: {e}")
                    )

        self.stdout.write(self.style.SUCCESS("\n=== Setup Completed ==="))
        self.stdout.write("\n📍 Available endpoints:")

        domains = Domain.objects.select_related("tenant").all()
        for domain in domains:
            self.stdout.write(
                f"  • http://{domain.domain}:8000 ({domain.tenant.schema_name})"
            )

        self.stdout.write("\n🔑 Default credentials:")
        self.stdout.write(f"  • Public: {public_owner}")
        if create_demo:
            self.stdout.write(f"  • Demo: {demo_owner_email} / {demo_password}")

        demo_owner_tenant = demo_owner.tenants.last()
        with tenant_context(demo_owner_tenant):
            self.stdout.write(" Updating Demo Owner Permissions...")
            demo_owner.tenant_perms.is_staff = True
            demo_owner.tenant_perms.is_superuser = True
            demo_owner.tenant_perms.save()
            self.stdout.write(" Demo Owner Permissions Updated")
