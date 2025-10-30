# teams/ AGENTS.md

Teams Module

## Module Overview

This module manages hierarchical teams within a tenant. Supports parent-child teams, soft delete, and standard CRUD via service layer.

- Team hierarchy (self-referential `parent`)
- Unique team names (per tenant schema)
- Soft delete pattern (`is_active`)
- Service layer for business logic
- Role-based permissions (manager/owner for writes)
- Tenant-aware operations

## Files Structure

```
teams/
├── __init__.py
├── apps.py
├── models.py              # Team model
├── serializers.py         # DRF serializer
├── services.py            # Business logic (TeamService)
├── views.py               # API views (TeamViewSet)
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_team_parent.py
└── tests/
    ├── test_services.py
    └── test_views.py
```

## Key Components

### 1. Model (`models.py`)

```python
class Team(BaseModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="sub_teams",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
```

- `parent`: Self-referential hierarchy
- `name`: Unique within tenant schema
- `is_active`: Soft delete flag

### 2. Service (`services.py`)

```python
class TeamService(BaseService):
    def create_object(self, name: str, description: str = None, **kwargs) -> Team: ...
    def update_object(self, instance: Team, **kwargs) -> Team: ...
    def delete_object(self, instance: Team) -> None:  # Soft delete
        ...
```

- Uses `update_fields` for efficient updates
- Delete performs soft delete (`is_active=False`)

### 3. API (`views.py`)

```python
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.filter(is_active=True).order_by("-created_on")
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsMinimumManagerOrReadOnly]
    service_class = TeamService()
```

Endpoints:
- GET `/api/teams/` — List active teams
- POST `/api/teams/` — Create team (manager+)
- GET `/api/teams/{id}/` — Detail
- PUT/PATCH `/api/teams/{id}/` — Update (manager+)
- DELETE `/api/teams/{id}/` — Soft delete (manager+)

Permissions:
- Read: any authenticated user
- Write: `manager` or `owner` (via `IsMinimumManagerOrReadOnly`)

## Common Patterns

### Tenant-Aware Usage

```python
from django_tenants.utils import tenant_context
from tenants.models import Client
from teams.services import TeamService

tenant = Client.objects.get(schema_name="evilcorp")

with tenant_context(tenant):
    service = TeamService()
    root = service.create_object(name="Engineering")
    backend = service.create_object(name="Backend", parent=root)
```

### Soft Delete Only

```python
service.delete_object(team)   # team.is_active = False
```

### Query Active Teams

```python
Team.objects.filter(is_active=True)
```

## Testing Guidelines

- Base mixins: `TenantTestCaseMixin`, `AuthenticatedTenantTestMixin`
- Coverage target: 85%

Suggested cases:
- Create team with/without parent
- Update team name/description
- Soft delete marks `is_active=False` and hides from default queryset
- Permission matrix in views (employee forbidden to write)

Commands:
```bash
uv run python manage.py test teams
uv run coverage run --source=teams manage.py test teams
uv run coverage report -m
```

## Common Tasks

### Add a New Field

```python
# models.py
class Team(BaseModel):
    # ...
    slack_channel = models.CharField(max_length=100, blank=True, null=True)
```

```bash
uv run python manage.py makemigrations teams
uv run python manage.py migrate_schemas
```

```python
# serializers.py
class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "parent", "description", "slack_channel"]
        read_only_fields = ["id", "is_active", "created_on", "updated_on"]
```

## Security Considerations

- Tenant isolation: always operate within `tenant_context()`
- Soft delete only: no hard delete in services
- Role-based writes: guarded by `IsMinimumManagerOrReadOnly`

## Quick Commands

```bash
# Run teams tests
uv run python manage.py test teams

# Migrations (tenant-aware)
uv run python manage.py makemigrations teams
uv run python manage.py migrate_schemas

# Swagger
http://localhost:8000/api/schema/swagger-ui/#/teams
# ReDoc
http://localhost:8000/api/schema/redoc/#tag/teams
```

---

**Coverage Target:** 85%
**Last Updated:** 2025-10-30


