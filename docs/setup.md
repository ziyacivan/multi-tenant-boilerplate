## Kurulum Adımları

### Ana Tenant'ın Oluşturulması (Sistem Tenant'ı)
Ana projenin tenant olarak tanınması ve bu şekilde sürecin başlatılması gerekmekte. Bunun için aşağıdaki adımlar izlenebilir:

```py
from tenant_users.tenants.utils import create_public_tenant

create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")
```

Bu komut, public schema içerisinde, public tenant ve public domain'i oluşturacaktır.

### Müşteri Tenant'ın Oluşturulması
Birinci adım olarak müşteri için bir süper kullanıcı oluşturulmalıdır.

```py
from users.models import User

user = User.objects.create_user(email="user@evilcorp.com", password="password", is_staff=True)
```

Kullanıcı oluşturulduktan sonra `Tenant` kaydı şu şekilde açılmalıdır:

```py
from tenant_users.tenants.tasks import provision_tenant
from users.models import User

provision_tenant_owner = User.objects.get(email="user@evilcorp.com")


tenant, domain = provision_tenant("EvilCorp", "evilcorp", provision_tenant_owner)
```

Bu adımlar uygulandıktan sonra şema otomatik olarak oluşturulacaktır ve migrate edilecektir.

### Müşteri Tenant'ının Silinmesi
```py
from tenants.models import Client

evil = Client.objects.get(slug="evil")
evil.delete_tenant()
```

### Müşteri Tenant Kullanıcısının Silinmesi
```py
from users.models import User

user = User.objects.get(email="user@domain.com")
User.objects.delete_user(user)
```

### Tenant Bağlantısı Olmayan Kullanıcının Silinmesi
```
from users.models import User

user = User.objects.get(email="user@domain.com")
user.delete(force_drop=True)
```

### Bir Tenant'a Yeni Bir Kullanıcı Eklenmesi
```py
from tenants.models import Client
from users.models import User

user = User.objects.get(email="user@domain.com")
evil = Client.objects.get(slug="evil")
evil.add_user(user)
```

### Tenant Schema'sı İçerisinde Operasyonlar
```py
from django_tenants.utils import tenant_context

# 1. Tenant nesnesini bir değişkene atayın
last_tenant = user.tenants.last()

# 2. tenant_context'e Tenant nesnesinin kendisini verin
if last_tenant:
    with tenant_context(last_tenant):
        print(f"'{last_tenant.schema_name}' şemasına geçildi.")
        
        # Kullanıcıyı yeniden çekmek bazen cache sorunlarını önler, ama genellikle gerekmeyebilir.
        # current_user = User.objects.get(pk=user.pk)
        
        user.tenant_perms.is_staff = True
        user.tenant_perms.is_superuser = True
        user.tenant_perms.save()
        
        print(f"'{user.email}' kullanıcısının izinleri güncellendi.")
else:
    print("Kullanıcı herhangi bir kiracıya atanmamış.")
```