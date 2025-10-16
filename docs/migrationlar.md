### Migration yönetimi nasıl yapılır?

Eğer shared app'lerde bir değişiklik yapılıyorsa aşağıdaki komut çalıştırılmalı:
```shell
python manage.py migrate_schemas --shared
```

Eğer tenant spesifik app'lerde bir değişiklik yapılıyorsa aşağıdaki komut çalıştırılmalı:
```shell
python manage.py migrate_schemas
```

Migration file oluşturmak için default `makemigrations` komutu geçerlidir.