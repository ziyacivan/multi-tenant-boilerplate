### Tenant yönetimi nasıl yapılır?

Ana uygulamamızın erişilebilir olması için başlangıçta main bir `Tenant` oluşturmamız gerekmektedir:
```py
from customers.models import Client, Domain

# create your public tenant
tenant = Client(schema_name='public',
                name='HRM',)
tenant.save()

# Add one or more domains for the tenant
domain = Domain()
domain.domain = 'my-domain.com' # don't add your port or www here! on a local server you'll want to use localhost here
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

### Bir müşteri için tenant yönetimi nasıl yapılır?

Bir müşterinin sistemde tanıtılabilmesi için aşağıdaki adımlar izlenmelidir:
```py
from customers.models import Client, Domain

# create your first real tenant
tenant = Client(schema_name='tenant1',
                name='Fonzy Tenant')
tenant.save() # migrate_schemas automatically called, your tenant is ready to be used!

# Add one or more domains for the tenant
domain = Domain()
domain.domain = 'tenant.my-domain.com' # don't add your port or www here!
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

### Bir müşterinin sistemden kaldırılması nasıl yapılır?

1. Mevcut yapımızla remote'den veritabanına bağlanarak ilgili schema'nın düşürülmesi yeterlidir fakat bu veri kaybına da yol açacaktır.
2. Bir diğer seçenek `Client` kaydının `is_active` değerini `False` olarak işaretlemektir.
3. `auto_drop_schema` değeri `True` olarak işaretlenerek, Django ORM ile doğrudan bir servis aracılığıyla da yapılabilir fakat bu yine schema'yı düşüreceği için
veri kaybına yol açacaktır.

### Users modülünün işlevi nasıl çalışır?
`users` modülü ve içerisinde barınan `User` kayıtları `config/settings.py` içerisinde `TENANT_APPS` listesine dahil edildiği için aslında
her bir müşterinin kendine ait `users` tablosu vardır ve birbirlerinden izoledir.