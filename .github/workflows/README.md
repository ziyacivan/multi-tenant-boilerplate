# GitHub Actions Workflows

Bu dizin, projenin GitHub Actions CI/CD pipeline'larını içerir.

## Mevcut Workflow'lar

### ci.yml - CI Pipeline

**Tetikleyiciler:**
- `master` branch'ına push
- `master` branch'ına pull request

**İşler:**
1. **Code Formatting Check** - Black ve isort ile kod formatı kontrolü
2. **Tests & Coverage** - Django testleri ve %80 minimum coverage kontrolü

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

# Testler ve coverage
uv run coverage run --source='.' manage.py test --keepdb
uv run coverage report --fail-under=80
```

## Sorun Giderme

Pipeline başarısız olursa:

1. **Formatting hatası:** Yerel olarak `black .` ve `isort .` çalıştırın
2. **Test hatası:** `python manage.py test` ile yerel testleri çalıştırın
3. **Coverage düşük:** `coverage html` ile detaylı rapor oluşturun

Daha fazla bilgi için [CI Pipeline Dokümantasyonu](../../docs/ci-pipeline.md)'na bakın.

