# HRM API - Multi-tenant Human Resource Management System

A modern, scalable multi-tenant Human Resource Management System API built with Django 5.2.7 and django-tenants. Each tenant (company) operates in its own PostgreSQL schema, ensuring complete data isolation and security.

## 🚀 Features

- **Multi-tenant Architecture**: Complete data isolation using PostgreSQL schema-per-tenant approach
- **JWT Authentication**: Secure token-based authentication with refresh token rotation
- **Employee Management**: Comprehensive employee profiles with personal details
- **Team & Title Management**: Organizational structure management
- **Async Task Processing**: Celery + Redis for background jobs
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Docker Support**: Full containerization for easy deployment
- **Comprehensive Testing**: High test coverage with parallel CI pipeline
- **Tenant-aware File Storage**: Isolated media storage per tenant

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.13**
- **Django 5.2.7** - Web framework
- **Django REST Framework 3.16.1** - REST API
- **django-tenants 3.9.0** - Multi-tenancy support
- **django-tenant-users 2.2.1** - User management for tenants
- **PostgreSQL 16** - Database (schema-per-tenant)

### Authentication & Security
- **djangorestframework-simplejwt 5.5.1** - JWT authentication
- **bcrypt 5.0.0** - Password hashing
- **django-cors-headers 4.9.0** - CORS handling

### Task Queue & Caching
- **Celery 5.5.3** - Distributed task queue
- **Redis** - Message broker and result backend

### Development Tools
- **uv** - Fast Python package manager
- **Black** - Code formatter
- **isort** - Import sorter
- **coverage** - Test coverage
- **model-bakery** - Test fixtures
- **drf-spectacular** - OpenAPI schema generation

## 📋 Prerequisites

- Python 3.13+
- PostgreSQL 15+
- Redis
- Docker & Docker Compose (optional, for containerized setup)
- [uv](https://github.com/astral-sh/uv) package manager

## 🚀 Quick Start

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multi-tenant-boilerplate
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   # Shared apps migrations
   docker-compose exec web uv run python manage.py migrate_schemas --shared
   
   # Tenant apps migrations
   docker-compose exec web uv run python manage.py migrate_schemas
   ```

5. **Create public tenant** (first-time setup)
   ```bash
   docker-compose exec web uv run python manage.py shell
   ```
   ```python
   >>> from tenant_users.tenants.utils import create_public_tenant
   >>> create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")
   >>> exit()
   ```

6. **Access the API**
   - API: http://localhost:8000/api/v1/
   - Swagger UI: http://localhost:8000/api/v1/schema/swagger-ui/
   - ReDoc: http://localhost:8000/api/v1/schema/redoc/

### Option 2: Native Setup

1. **Install dependencies**
   ```bash
   uv sync --extra dev
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL and Redis credentials
   ```

3. **Run migrations**
   ```bash
   uv run python manage.py migrate_schemas --shared
   uv run python manage.py migrate_schemas
   ```

4. **Create public tenant**
   ```bash
   uv run python manage.py shell
   ```
   ```python
   >>> from tenant_users.tenants.utils import create_public_tenant
   >>> create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")
   >>> exit()
   ```

5. **Start development server**
   ```bash
   uv run python manage.py runserver
   ```

6. **Start Celery worker** (in a separate terminal)
   ```bash
   uv run celery -A config worker -l info
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=hrm_db
DB_USER=hrm_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Email (Gmail example)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Database Setup

The project uses PostgreSQL with schema-per-tenant architecture:

- **Public Schema**: Contains shared apps (tenants, users)
- **Tenant Schemas**: Each tenant has its own schema (employees, titles, teams)

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/v1/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/v1/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/v1/schema/

### API Endpoints

#### Public Endpoints (No Authentication Required)

- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/refresh/` - Refresh access token
- `POST /api/v1/auth/verify-email/` - Verify email address
- `POST /api/v1/auth/resend-verification/` - Resend verification email
- `POST /api/v1/auth/password-reset/` - Request password reset
- `POST /api/v1/auth/password-reset-confirm/` - Confirm password reset

#### Tenant Endpoints (Authentication Required)

- `GET /api/v1/employees/` - List employees
- `POST /api/v1/employees/` - Create employee
- `GET /api/v1/employees/{id}/` - Get employee details
- `PUT /api/v1/employees/{id}/` - Update employee
- `DELETE /api/v1/employees/{id}/` - Delete employee

- `GET /api/v1/titles/` - List job titles
- `POST /api/v1/titles/` - Create job title
- `GET /api/v1/titles/{id}/` - Get title details
- `PUT /api/v1/titles/{id}/` - Update title
- `DELETE /api/v1/titles/{id}/` - Delete title

- `GET /api/v1/teams/` - List teams
- `POST /api/v1/teams/` - Create team
- `GET /api/v1/teams/{id}/` - Get team details
- `PUT /api/v1/teams/{id}/` - Update team
- `DELETE /api/v1/teams/{id}/` - Delete team

### Authentication

All tenant endpoints require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <access_token>
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
uv run python manage.py test

# Run tests for specific module
uv run python manage.py test employees
uv run python manage.py test auth

# Run with coverage
uv run coverage run --source=employees manage.py test employees
uv run coverage report

# Generate HTML coverage report
uv run coverage html
open htmlcov/index.html
```

### Coverage Targets

Minimum coverage rates:
- **auth**: 85%
- **employees**: 80%
- **titles**: 95%
- **teams**: 95%

### CI Pipeline

The project includes a GitHub Actions CI pipeline that:
- Checks code formatting
- Runs tests in parallel for each module
- Enforces coverage thresholds

## 🏗️ Project Structure

```
multi-tenant-boilerplate/
├── auth/              # Authentication app
│   ├── services.py    # Business logic
│   ├── views.py       # API endpoints
│   ├── serializers.py # Request/response serializers
│   └── tests/         # Test suite
├── config/            # Django settings
│   ├── settings.py    # Main configuration
│   ├── urls.py        # Tenant URLs
│   └── public_urls.py # Public URLs
├── employees/         # Employee management
├── teams/             # Team management
├── titles/            # Job title management
├── tenants/           # Tenant management
├── users/             # User model
├── utils/             # Shared utilities
│   ├── models.py      # BaseModel
│   ├── services.py    # BaseService
│   └── storages.py    # Tenant-aware storage
├── templates/         # Email templates
├── docs/              # Documentation
├── docker-compose.yml # Docker configuration
└── pyproject.toml     # Project dependencies
```

## 🏛️ Architecture

### Multi-Tenant Pattern

The project uses **schema-per-tenant** architecture:

- Each tenant has its own PostgreSQL schema
- Complete data isolation between tenants
- Shared schema for tenant and user management
- Domain-based routing via custom middleware

### Service Layer Pattern

Business logic is separated into service classes:

```python
from utils.interfaces import BaseService

class EmployeeService(BaseService):
    def create_object(self, user, first_name, last_name, **kwargs):
        """Creates a new employee."""
        return Employee.objects.create(...)
```

### Base Models

All models extend `BaseModel` which provides:
- `created_on` - Creation timestamp
- `updated_on` - Last update timestamp
- `attributes` - JSON field for flexible data

## 🔧 Development

### Code Formatting

```bash
# Format code
uv format

# Check formatting
uv format --check
```

### Creating Migrations

```bash
# Create migration
uv run python manage.py makemigrations <app_name>

# Apply migrations (tenant-aware)
uv run python manage.py migrate_schemas --shared  # Shared apps first
uv run python manage.py migrate_schemas            # Tenant apps
```

### Django Shell

```bash
# Enter Django shell
uv run python manage.py shell

# Work with tenant context
from django_tenants.utils import tenant_context
from tenants.models import Client

tenant = Client.objects.get(schema_name="company")
with tenant_context(tenant):
    employees = Employee.objects.all()
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web
docker-compose logs -f celery_worker

# Execute commands
docker-compose exec web uv run python manage.py <command>
docker-compose exec web bash

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📖 Documentation

Additional documentation is available in the `docs/` directory:

- [Setup Guide](docs/setup.md)
- [Multi-Tenant Architecture](docs/tenantlar.md)
- [Migrations Guide](docs/migrationlar.md)
- [Docker Deployment](docs/docker.md)
- [CI Pipeline](docs/ci-pipeline.md)
- [Create Company Flow](docs/flows/create_company.md)
- [Tenant-Aware Storage](docs/tenant-aware-storage.md)

## 🔐 Security Considerations

- **JWT Tokens**: Access token (60 min), Refresh token (24 hours)
- **Token Rotation**: New token generated on each refresh
- **Password Hashing**: bcrypt with secure defaults
- **Schema Isolation**: Complete data separation per tenant
- **CORS**: Configurable allowed origins
- **Rate Limiting**: Throttling on sensitive endpoints

## 🚢 Deployment

### Production Checklist

1. Set `DEBUG=False` in environment
2. Configure `ALLOWED_HOSTS`
3. Set secure `SECRET_KEY`
4. Configure production database
5. Set up SSL/TLS certificates
6. Configure email backend
7. Set up static file serving
8. Configure Celery workers
9. Set up monitoring and logging

### Docker Production

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec web uv run python manage.py migrate_schemas --shared
docker-compose exec web uv run python manage.py migrate_schemas

# Collect static files
docker-compose exec web uv run python manage.py collectstatic --noinput
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style guidelines
4. Write tests for new functionality
5. Ensure all tests pass and coverage meets thresholds
6. Format code with `uv format`
7. Commit your changes (`git commit -m 'feat: add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- Follow Black formatting (line-length=88)
- Use isort for import sorting
- Add type hints where possible
- Write docstrings in Google style
- Follow Django best practices

## 📝 License

This project is licensed under the terms specified in the LICENSE file.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Django Tenants community
- Django REST Framework team
- All contributors

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in `docs/`
- Review `AGENTS.md` for development guidelines

---

**Version**: 0.1.0  
**Last Updated**: 2025-01-26  
**Python**: 3.13  
**Django**: 5.2.7
