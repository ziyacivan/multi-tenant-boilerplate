# GitHub Actions Workflows

This directory contains the GitHub Actions CI/CD pipelines for the project.

## Available Workflows

### ci.yml - CI Pipeline

**Triggers:**
- Push to `master` branch
- Pull request to `master` branch

**Jobs:**
1. **Code Formatting Check** - Code format check with Black and isort
2. **Module-Based Test Jobs** (Parallel):
   - **Test Auth Module** - Auth module tests (85% coverage)
   - **Test Tenants Module** - Tenants module tests (80% coverage)
   - **Test Users Module** - Users module tests (75% coverage)
   - **Test Employees Module** - Employees module tests (80% coverage)
   - **Test Utils Module** - Utils module tests (90% coverage)
   - **Test Titles Module** - Titles module tests (95% coverage)
3. **Test Summary** - Combines all coverage reports

**Detailed information:** [CI Pipeline Documentation](../../docs/ci-pipeline.md)

## Local Usage

### Install Formatters
```bash
uv sync --extra dev
```

### Format Code (Run before CI)
```bash
uv format
# Or individually:
black .
isort .
```

### Run Checks
```bash
# Formatting check
uv format --check
# Or individually:
black --check --diff .
isort --check-only --diff .

# All tests and general coverage
uv run coverage run manage.py test --keepdb
uv run coverage report

# Module-based tests (like in CI)
uv run coverage run --source='auth' manage.py test auth --keepdb
uv run coverage report --fail-under=85

uv run coverage run --source='tenants' manage.py test tenants --keepdb
uv run coverage report --fail-under=80

uv run coverage run --source='users' manage.py test users --keepdb
uv run coverage report --fail-under=75

uv run coverage run --source='employees' manage.py test employees --keepdb
uv run coverage report --fail-under=80

uv run coverage run --source='titles' manage.py test titles --keepdb
uv run coverage report --fail-under=95

uv run coverage run --source='utils' manage.py test utils --keepdb
uv run coverage report --fail-under=90

# ... similarly for other modules
```

## Troubleshooting

If the pipeline fails:

1. **Formatting error:** Run `uv format` locally (or `black .` and `isort .`)
2. **Test error:** Run local tests with `python manage.py test`
3. **Low coverage:** Generate detailed report with `coverage html`

For more information, see the [CI Pipeline Documentation](../../docs/ci-pipeline.md).
