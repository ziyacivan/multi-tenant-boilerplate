# CI/CD Pipeline Dokümantasyonu

Bu doküman, projenin GitHub Actions CI/CD pipeline yapısını açıklar.

## Genel Bakış

HRM API projesi için otomatik test ve kod kalitesi kontrolü sağlayan bir CI/CD pipeline sistemi kurulmuştur. Pipeline, aşağıdaki durumlarda otomatik olarak çalışır:

- `master` branch'ına yapılan her push işleminde
- `master` branch'ına yönelik her pull request açıldığında veya güncellendiğinde
- Pull request'lerin `master` branch'ına merge edilmesi sırasında

## Pipeline İşleri (Jobs)

Pipeline **paralel çalışan** işler içerir: **Formatting Check** ve **Modül Bazlı Test Jobs**

### 1. Code Formatting Check

**Amaç:** Kod formatlaması ve import sıralamasının standartlara uygun olup olmadığını kontrol eder.

**Kullanılan Araçlar:**
- **black**: Python kod formatlayıcı (PEP 8 uyumlu)
- **isort**: Import ifadelerini alfabetik ve kategorik olarak düzenler

**Kontroller:**
```bash
black --check --diff .
isort --check-only --diff .
```

**Başarısızlık Durumu:** Kod formatı kurallara uygun değilse pipeline başarısız olur.

### 2. Modül Bazlı Test Jobs (Paralel)

**Amaç:** Her Django modülünü ayrı ayrı test eder ve modül bazlı coverage limitleri uygular.

**Modüller ve Coverage Limitleri:**
- **auth**: %85 (kritik güvenlik modülü)
- **tenants**: %80 (çok kiracılı mimari)
- **users**: %75 (temel kullanıcı yönetimi)
- **employees**: %80 (iş süreçleri)
- **utils**: %90 (yardımcı fonksiyonlar)

**Servisler:**
- Her job için ayrı PostgreSQL 15 container

**Test Süreci (Her Modül İçin):**
1. PostgreSQL servisinin hazır olması beklenir
2. Django test ortamı için `.env` dosyası oluşturulur
3. Sadece ilgili modül testleri çalıştırılır: `coverage run --source='MODULE' manage.py test MODULE --keepdb`
4. Modül bazlı coverage raporu oluşturulur ve belirlenen minimum kontrol edilir
5. Coverage raporu GitHub Actions artifacts'a yüklenir

**Paralel Çalışma:**
- Tüm test job'ları `formatting` job'ı tamamlandıktan sonra **paralel** olarak başlar
- Her job farklı runner'da çalışır
- Toplam pipeline süresi: en yavaş job'ın süresi

### 3. Test Summary

**Amaç:** Tüm modül coverage raporlarını birleştirir ve genel özet oluşturur.

**Süreç:**
1. Tüm modül coverage raporları indirilir
2. Coverage raporları birleştirilir
3. Genel coverage raporu oluşturulur
4. Pull request'lerde coverage raporu yorum olarak eklenir

**Başarısızlık Durumu:** 
- Herhangi bir modül testi başarısız olursa
- Herhangi bir modül coverage'ı belirlenen limitin altına düşerse

## Konfigürasyon

### pyproject.toml

Proje kök dizinindeki `pyproject.toml` dosyasında tüm araçlar için yapılandırma bulunur:

#### Black Ayarları
```toml
[tool.black]
line-length = 88
target-version = ['py313']
```

#### isort Ayarları
```toml
[tool.isort]
profile = "black"
line_length = 88
known_django = ["django"]
known_first_party = ["auth", "config", "employees", "tenants", "users", "utils"]
```

#### Coverage Ayarları
```toml
[tool.coverage.run]
source = ["."]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "manage.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## Yerel Geliştirme

### Formatters'ı Yükleme

```bash
uv pip install black isort coverage
```

veya dev dependencies ile:

```bash
uv sync --extra dev
```

### Kod Formatlaması

Kodunuzu commit etmeden önce formatlamak için:

```bash
# Tüm kodu formatla
black .

# Import'ları düzenle
isort .
```

### Formatı Kontrol Etme

CI'da çalışacak kontrolleri yerel olarak test etmek için:

```bash
# Black kontrolü
black --check --diff .

# isort kontrolü
isort --check-only --diff .
```

### Testleri Coverage ile Çalıştırma

#### Tüm Modülleri Test Etme
```bash
# Dev dependencies'leri kur (coverage dahil)
uv sync --extra dev

# Tüm testleri coverage ile çalıştır
uv run coverage run manage.py test --keepdb

# Genel coverage raporunu görüntüle
uv run coverage report

# Detaylı HTML rapor oluştur
uv run coverage html
# Rapor: htmlcov/index.html
```

#### Modül Bazlı Test Etme (CI'daki gibi)
```bash
# Auth modülü (85% minimum)
uv run coverage run --source='auth' manage.py test auth --keepdb
uv run coverage report --fail-under=85

# Tenants modülü (80% minimum)
uv run coverage run --source='tenants' manage.py test tenants --keepdb
uv run coverage report --fail-under=80

# Users modülü (75% minimum)
uv run coverage run --source='users' manage.py test users --keepdb
uv run coverage report --fail-under=75

# Employees modülü (80% minimum)
uv run coverage run --source='employees' manage.py test employees --keepdb
uv run coverage report --fail-under=80

# Utils modülü (90% minimum)
uv run coverage run --source='utils' manage.py test utils --keepdb
uv run coverage report --fail-under=90
```

## Pipeline Sonuçlarını Görüntüleme

1. GitHub repository'nizde **Actions** sekmesine gidin
2. İlgili workflow çalıştırmasını seçin
3. Her job'un detaylarını ve loglarını inceleyebilirsiniz
4. Coverage raporunu **Artifacts** bölümünden indirebilirsiniz

## Pull Request Workflow

1. Feature branch'inde çalışın
2. Commit etmeden önce `black .` ve `isort .` komutlarını çalıştırın
3. Pull request açın
4. CI pipeline otomatik olarak çalışır:
   - Formatting kontrolü yapılır
   - Testler çalıştırılır ve coverage kontrol edilir
5. Pipeline başarılı olursa PR merge edilebilir
6. Coverage raporu PR'a yorum olarak eklenir

## Sorun Giderme

### Formatting Hataları

Pipeline'da formatting hatası alırsanız:

```bash
# Yerel olarak formatla
black .
isort .

# Değişiklikleri commit et
git add .
git commit -m "Fix formatting"
git push
```

### Coverage Düşük

Coverage %80'in altındaysa:

1. Hangi dosyaların coverage'ı düşük olduğunu kontrol edin:
   ```bash
   uv run coverage report
   ```

2. Eksik testleri yazın

3. Coverage HTML raporunu inceleyin:
   ```bash
   uv run coverage html
   open htmlcov/index.html
   ```

### Test Hataları

Testler başarısız olursa:

1. Yerel ortamda testleri çalıştırın:
   ```bash
   python manage.py test
   ```

2. Hataları düzeltin

3. Commit ve push edin

## Best Practices

1. **Her commit'ten önce formatlanmış kod:** `black .` ve `isort .` çalıştırın
2. **Testleri yerel olarak çalıştırın:** Push etmeden önce testlerin geçtiğinden emin olun
3. **Coverage'ı takip edin:** Yeni kod yazarken test yazmayı unutmayın
4. **Migration dosyalarını commit edin:** Migration dosyaları coverage'dan hariç tutulmuştur
5. **CI loglarını inceleyin:** Pipeline başarısız olursa detaylı logları okuyun

## Faydalı Linkler

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

