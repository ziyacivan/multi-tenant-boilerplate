employee.photo = file
# 📁 Tenant-Aware Storage

## Ne Yaptık?

Her şirketin kendi dosyalarının ayrı bir klasörde tutulduğu **tenant-aware storage** yapısını devreye aldık. Böylece herhangi bir şirket (örneğin EvilCorp), başka bir şirketin (örneğin AcmeCorp) görsel ya da dokümanlarını göremez.

```
mediafiles/
├── evilcorp/        ← EvilCorp'un tüm dosyaları burada
│   └── employees/photos/... 
├── acmecorp/        ← AcmeCorp'un dosyaları burada
│   └── employees/photos/...
└── ...
```

- **API değişmedi.** Çalışan profil fotoğrafı yüklemek için hâlâ `PATCH /api/v1/employees/{id}/` endpoint'ini `multipart/form-data` ile kullanıyoruz.
- İstek sırasında tenant domain'i (ör: `https://evilcorp.localhost:8000`) üzerinden çağrı yapıldığında dosya otomatik olarak doğru klasöre düşüyor.
- Response içindeki `photo` alanında dönen URL artık tenant adını içeriyor: `https://evilcorp.localhost:8000/media/evilcorp/employees/photos/<dosya>`