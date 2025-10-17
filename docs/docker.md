# 🐳 Docker ile HRM API Kullanım Kılavuzu

## 📋 Ön Gereksinimler

Sisteminizde aşağıdaki yazılımların kurulu olması gerekmektedir:

- **Docker Desktop** (macOS/Windows) veya **Docker Engine** (Linux)
  - [Docker Desktop İndirme](https://www.docker.com/products/docker-desktop/)
  - Minimum: Docker 20.10+
- **Git**

Docker'ın çalıştığını kontrol edin:
```bash
docker --version
docker-compose --version
```

## 🚀 İlk Kurulum

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/your-org/hrm-api.git
cd hrm-api
```

### 2. Environment Dosyasını Oluşturun

```bash
cp .env.example .env
```

### 3. API'yi Başlatın

```bash
docker-compose up
```

İlk çalıştırmada:
- Docker image'ları indirilecek (~2-3 dakika)
- Dependencies yüklenecek
- Veritabanı oluşturulacak
- Migration'lar çalışacak
- Public ve Demo tenant'lar otomatik oluşturulacak

**Başarılı başlatma mesajı:**
```
✅ PostgreSQL is ready!
📦 Running migrations for public schema...
🏢 Setting up development tenants...
✓ Public tenant created
✓ Demo Company tenant created
🚀 Starting server...
Starting development server at http://0.0.0.0:8000/
```

## 🌐 API Erişimi

### Temel URL'ler

| Tenant | URL | Açıklama |
|--------|-----|----------|
| Public | `http://localhost:8000` | Ana sistem API'si |
| Demo | `http://demo.localhost:8000` | Demo şirket API'si |

### API Dokümantasyonu

API dokümantasyonuna Swagger UI üzerinden erişebilirsiniz:

- **Swagger UI**: http://localhost:8000/api/v1/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/v1/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/v1/schema/

## 🔑 Test Kullanıcıları

Geliştirme ortamında kullanabileceğiniz hazır test kullanıcıları:

### Public Tenant
- **Email**: `admin@localhost.com`
- **Password**: _(create_public_tenant tarafından otomatik oluşturulur)_

### Demo Tenant
- **Email**: `demo@demo.local`
- **Password**: `demo123`

## 🛠️ Günlük Kullanım Komutları

### API'yi Başlatma/Durdurma

```bash
# Başlat (foreground)
docker-compose up

# Başlat (background)
docker-compose up -d

# Durdur
docker-compose down

# Durdur ve veritabanını sil (fresh start)
docker-compose down -v
```

### Logları İzleme

```bash
# Tüm servislerin logları
docker-compose logs -f

# Sadece API logları
docker-compose logs -f web

# Son 100 satır
docker-compose logs --tail=100 web
```

## 🐛 Sorun Giderme

### Port Çakışması

**Sorun:** "Port 8000 is already in use"

**Çözüm:**
```bash
# Portun kim tarafından kullanıldığını kontrol edin
lsof -i :8000

# Alternatif: docker-compose.yml'de portu değiştirin
# ports: "8001:8000"
```

### Veritabanı Bağlantı Hatası

**Sorun:** "Could not connect to database"

**Çözüm:**
```bash
# Container'ları yeniden başlatın
docker-compose down
docker-compose up

# PostgreSQL loglarını kontrol edin
docker-compose logs db
```

### CORS Hatası

**Sorun:** "Access-Control-Allow-Origin" hatası

**Çözüm:** `.env` dosyasında frontend URL'inizi ekleyin:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Sonra container'ı yeniden başlatın:
```bash
docker-compose restart web
```

### Migration Hatası

**Sorun:** Migration hataları

**Çözüm:**
```bash
# Fresh start
docker-compose down -v
docker-compose up --build
```

### Faydalı Komutlar

```bash
# Django shell'e erişim
docker-compose exec web uv run python manage.py shell

# Yeni superuser oluştur
docker-compose exec web uv run python manage.py createsuperuser

# Database backup
docker-compose exec db pg_dump -U hrm_user hrm_db > backup.sql

# Database restore
docker-compose exec -T db psql -U hrm_user hrm_db < backup.sql

# Container'a shell ile bağlan
docker-compose exec web bash
```

### Environment Variables

`.env` dosyasında değiştirebileceğiniz önemli değişkenler:

```env
# Debug modu (development için true)
DEBUG=True

# JWT token süreleri (dakika)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS ayarları
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database ayarları
DB_NAME=hrm_db
DB_USER=hrm_user
DB_PASSWORD=hrm_password
```
