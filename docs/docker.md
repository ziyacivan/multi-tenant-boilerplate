# 🐳 Docker Guide for HRM API

## 📋 Prerequisites

The following software must be installed on your system:

- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
  - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Minimum: Docker 20.10+
- **Git**

Verify Docker is running:

```bash
docker --version
docker-compose --version
```

## 🚀 Initial Setup

### 1. Clone the Project

```bash
git clone https://github.com/your-org/hrm-api.git
cd hrm-api
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=hrm_db
DB_USER=hrm_user
DB_PASSWORD=secure_password
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. Start the API

```bash
docker-compose up
```

On first run:
- Docker images will be downloaded (~2-3 minutes)
- Dependencies will be installed
- Database will be created
- Migrations will run
- Public and Demo tenants will be automatically created

**Successful startup message:**
```
✅ PostgreSQL is ready!
📦 Running migrations for public schema...
🏢 Setting up development tenants...
✓ Public tenant created
✓ Demo Company tenant created
🚀 Starting server...
Starting development server at http://0.0.0.0:8000/
```

## 🌐 API Access

### Base URLs

| Tenant | URL | Description |
|--------|-----|-------------|
| Public | `http://localhost:8000` | Main system API |
| Demo | `http://demo.localhost:8000` | Demo company API |

### API Documentation

Access API documentation via Swagger UI:

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 🔑 Test Users

Ready-to-use test users for development environment:

### Public Tenant
- **Email**: `admin@localhost.com`
- **Password**: _(automatically created by create_public_tenant)_

### Demo Tenant
- **Email**: `demo@demo.local`
- **Password**: `demo123`

## 🛠️ Daily Usage Commands

### Starting/Stopping the API

```bash
# Start (foreground)
docker-compose up

# Start (background)
docker-compose up -d

# Stop
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

### Viewing Logs

```bash
# All services logs
docker-compose logs -f

# Only API logs
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web

# Specific service
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f celery
```

### Running Commands in Container

```bash
# Django shell
docker-compose exec web uv run python manage.py shell

# Create superuser
docker-compose exec web uv run python manage.py createsuperuser

# Run migrations
docker-compose exec web uv run python manage.py migrate_schemas --shared
docker-compose exec web uv run python manage.py migrate_schemas

# Run tests
docker-compose exec web uv run python manage.py test

# Run specific test
docker-compose exec web uv run python manage.py test employees.tests.test_services

# Bash access
docker-compose exec web bash
```

## 🐛 Troubleshooting

### Port Conflict

**Problem:** "Port 8000 is already in use"

**Solution:**
```bash
# Check what's using the port
lsof -i :8000

# Alternative: Change port in docker-compose.yml
# ports: "8001:8000"
```

### Database Connection Error

**Problem:** "Could not connect to database"

**Solution:**
```bash
# Restart containers
docker-compose down
docker-compose up

# Check PostgreSQL logs
docker-compose logs db

# Verify database is running
docker-compose ps
```

### CORS Error

**Problem:** "Access-Control-Allow-Origin" error

**Solution:** Add your frontend URL to `.env` file:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Then restart the container:

```bash
docker-compose restart web
```

### Migration Errors

**Problem:** Migration errors

**Solution:**
```bash
# Fresh start
docker-compose down -v
docker-compose up --build

# Or manually run migrations
docker-compose exec web uv run python manage.py migrate_schemas --shared
docker-compose exec web uv run python manage.py migrate_schemas
```

### Container Won't Start

**Problem:** Container exits immediately

**Solution:**
```bash
# Check logs
docker-compose logs web

# Rebuild images
docker-compose build --no-cache

# Remove and recreate
docker-compose down -v
docker-compose up --build
```

### Permission Errors

**Problem:** Permission denied errors

**Solution:**
```bash
# Fix file permissions (Linux/Mac)
sudo chown -R $USER:$USER .

# Or run with sudo (not recommended)
sudo docker-compose up
```

## 🔧 Useful Commands

### Database Operations

```bash
# Database backup
docker-compose exec db pg_dump -U hrm_user hrm_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Database restore
docker-compose exec -T db psql -U hrm_user hrm_db < backup.sql

# Database shell
docker-compose exec db psql -U hrm_user hrm_db

# List databases
docker-compose exec db psql -U hrm_user -l
```

### Container Management

```bash
# View running containers
docker-compose ps

# View container resource usage
docker stats

# Restart specific service
docker-compose restart web
docker-compose restart db
docker-compose restart redis

# Rebuild specific service
docker-compose build web

# Remove stopped containers
docker-compose rm

# View container details
docker-compose exec web env
```

### Development Tools

```bash
# Run code formatter
docker-compose exec web uv format

# Run linter
docker-compose exec web uv run black --check .
docker-compose exec web uv run isort --check-only .

# Run tests with coverage
docker-compose exec web uv run coverage run --source=employees manage.py test employees
docker-compose exec web uv run coverage report
```

## 📝 Environment Variables

Important variables you can modify in `.env` file:

```env
# Debug mode (true for development)
DEBUG=True

# JWT token lifetimes (minutes)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database settings
DB_NAME=hrm_db
DB_USER=hrm_user
DB_PASSWORD=hrm_password
DB_HOST=db
DB_PORT=5432

# Redis settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email settings (if configured)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Allowed hosts
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🔄 Updating the Application

### Update Code

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build
```

### Update Dependencies

```bash
# Update uv.lock
docker-compose exec web uv lock

# Rebuild with new dependencies
docker-compose build --no-cache web
docker-compose up -d
```

## 🧹 Cleanup

### Remove All Containers and Volumes

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Remove unused resources
docker system prune -a
```

### Reset Database

```bash
# Remove database volume
docker-compose down -v
docker volume rm multi-tenant-boilerplate_db_data

# Start fresh
docker-compose up
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Setup Guide](./setup.md)
- [Tenant Management](./tenants.md)
- [Migration Guide](./migrations.md)

## 🎯 Best Practices

1. **Always use `.env` file:** Never commit sensitive data
2. **Backup regularly:** Backup database before major changes
3. **Use volumes:** Persist data using Docker volumes
4. **Monitor logs:** Regularly check container logs
5. **Keep images updated:** Regularly update base images
6. **Use health checks:** Configure health checks for services
7. **Document changes:** Document any custom configurations
