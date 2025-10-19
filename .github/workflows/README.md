# GitHub Actions Workflows

Bu dizin, projenin GitHub Actions CI/CD pipeline'larını içerir.

## Mevcut Workflow'lar

### ci.yml - CI Pipeline

**Tetikleyiciler:**
- `master` branch'ına push
- `master` branch'ına pull request

**İşler:**
1. **Code Formatting Check** - Black ve isort ile kod formatı kontrolü
2. **Modül Bazlı Test Jobs** (Paralel):
   - **Test Auth Module** - Auth modülü testleri (%85 coverage)
   - **Test Tenants Module** - Tenants modülü testleri (%80 coverage)
   - **Test Users Module** - Users modülü testleri (%75 coverage)
   - **Test Employees Module** - Employees modülü testleri (%80 coverage)
   - **Test Utils Module** - Utils modülü testleri (%90 coverage)
3. **Test Summary** - Tüm coverage raporlarını birleştirir

**Detaylı bilgi:** [CI Pipeline Dokümantasyonu](../../docs/ci-pipeline.md)

## Yerel Kullanım

### Formatters'ı Kur
```bash
uv sync --extra dev
```

### Kod Formatla (CI'dan önce çalıştır)
```bash
black .
isort .
```

### Kontrolleri Çalıştır
```bash
# Formatting kontrolü
black --check --diff .
isort --check-only --diff .

# Tüm testler ve genel coverage
uv run coverage run manage.py test --keepdb
uv run coverage report

# Modül bazlı testler (CI'daki gibi)
uv run coverage run --source='auth' manage.py test auth --keepdb
uv run coverage report --fail-under=85

uv run coverage run --source='tenants' manage.py test tenants --keepdb
uv run coverage report --fail-under=80

# ... diğer modüller için benzer şekilde
```

## Sorun Giderme

Pipeline başarısız olursa:

1. **Formatting hatası:** Yerel olarak `black .` ve `isort .` çalıştırın
2. **Test hatası:** `python manage.py test` ile yerel testleri çalıştırın
3. **Coverage düşük:** `coverage html` ile detaylı rapor oluşturun

Daha fazla bilgi için [CI Pipeline Dokümantasyonu](../../docs/ci-pipeline.md)'na bakın.

