# CI/CD Pipeline Documentation

This document describes the GitHub Actions CI/CD pipeline structure for the project.

## Overview

An automated testing and code quality control CI/CD pipeline system has been set up for the HRM API project. The pipeline runs automatically in the following cases:

- On every push to the `master` branch
- When a pull request is opened or updated targeting the `master` branch
- During merge of pull requests into the `master` branch

## Pipeline Jobs

The pipeline contains **parallel running jobs**: **Formatting Check** and **Module-Based Test Jobs**

### 1. Code Formatting Check

**Purpose:** Checks if code formatting and import ordering comply with standards.

**Tools Used:**
- **black**: Python code formatter (PEP 8 compliant)
- **isort**: Organizes import statements alphabetically and categorically

**Checks:**
```bash
uv format --check
```

This runs both `black --check` and `isort --check-only` with the project's configuration.

**Failure Condition:** Pipeline fails if code format does not comply with rules.

### 2. Module-Based Test Jobs (Parallel)

**Purpose:** Tests each Django module separately and applies module-based coverage limits.

**Modules and Coverage Limits:**
- **auth**: 85% (critical security module)
- **tenants**: 80% (multi-tenant architecture)
- **users**: 75% (basic user management)
- **employees**: 80% (business processes)
- **titles**: 95% (job titles management)
- **utils**: 90% (helper functions)

**Services:**
- Separate PostgreSQL 15 container for each job

**Test Process (For Each Module):**
1. Wait for PostgreSQL service to be ready
2. Create `.env` file for Django test environment
3. Run only relevant module tests: `coverage run --source='MODULE' manage.py test MODULE --keepdb`
4. Generate module-based coverage report and check against minimum threshold
5. Upload coverage report to GitHub Actions artifacts

**Parallel Execution:**
- All test jobs start **in parallel** after the `formatting` job completes
- Each job runs on a different runner
- Total pipeline time: duration of the slowest job

### 3. Test Summary

**Purpose:** Combines all module coverage reports and creates a general summary.

**Process:**
1. Download all module coverage reports
2. Combine coverage reports
3. Generate general coverage report
4. Add coverage report as a comment on pull requests

**Failure Conditions:**
- Any module test fails
- Any module coverage falls below the specified limit

## Configuration

### pyproject.toml

Configuration for all tools is found in the `pyproject.toml` file in the project root:

#### Black Settings
```toml
[tool.black]
line-length = 88
target-version = ['py313']
exclude = '''
/(
    \.git
  | \.venv
  | \.uv
  | __pycache__
  | migrations
  | staticfiles
  | mediafiles
)/
'''
```

#### isort Settings
```toml
[tool.isort]
profile = "black"
line_length = 88
skip_glob = ["*/migrations/*", "staticfiles/*", "mediafiles/*"]
known_django = ["django"]
known_first_party = ["auth", "config", "employees", "tenants", "users", "utils"]
sections = ["FUTURE", "STDLIB", "DJANGO", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
```

#### Coverage Settings
```toml
[tool.coverage.run]
source = ["."]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "manage.py",
    "*/venv/*",
    "*/.venv/*",
    "*/.uv/*",
    "config/wsgi.py",
    "config/asgi.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

## Local Development

### Installing Formatters

```bash
# Install dev dependencies (includes formatters)
uv sync --extra dev
```

Or install individually:

```bash
uv pip install black isort coverage
```

### Code Formatting

Before committing your code, format it:

```bash
# Format all code (recommended)
uv format

# Or format individually
uv run black .
uv run isort .
```

### Checking Format

To test the checks that will run in CI locally:

```bash
# Check formatting (CI command)
uv format --check

# Or check individually
uv run black --check --diff .
uv run isort --check-only --diff .
```

### Running Tests with Coverage

#### Testing All Modules

```bash
# Install dev dependencies (coverage included)
uv sync --extra dev

# Run all tests with coverage
uv run coverage run manage.py test --keepdb

# View general coverage report
uv run coverage report

# Generate detailed HTML report
uv run coverage html
# Report: htmlcov/index.html
```

#### Module-Based Testing (Like CI)

```bash
# Auth module (85% minimum)
uv run coverage run --source='auth' manage.py test auth --keepdb
uv run coverage report --fail-under=85

# Tenants module (80% minimum)
uv run coverage run --source='tenants' manage.py test tenants --keepdb
uv run coverage report --fail-under=80

# Users module (75% minimum)
uv run coverage run --source='users' manage.py test users --keepdb
uv run coverage report --fail-under=75

# Employees module (80% minimum)
uv run coverage run --source='employees' manage.py test employees --keepdb
uv run coverage report --fail-under=80

# Titles module (95% minimum)
uv run coverage run --source='titles' manage.py test titles --keepdb
uv run coverage report --fail-under=95

# Utils module (90% minimum)
uv run coverage run --source='utils' manage.py test utils --keepdb
uv run coverage report --fail-under=90
```

## Viewing Pipeline Results

1. Go to the **Actions** tab in your GitHub repository
2. Select the relevant workflow run
3. You can review details and logs of each job
4. Download coverage report from the **Artifacts** section

## Pull Request Workflow

1. Work on a feature branch
2. Before committing, run `uv format` commands
3. Open a pull request
4. CI pipeline runs automatically:
   - Formatting check is performed
   - Tests are run and coverage is checked
5. If pipeline succeeds, PR can be merged
6. Coverage report is added as a comment to the PR

## Troubleshooting

### Formatting Errors

If you get a formatting error in the pipeline:

```bash
# Format locally
uv format

# Commit changes
git add .
git commit -m "Fix formatting"
git push
```

### Low Coverage

If coverage is below the threshold:

1. Check which files have low coverage:
   ```bash
   uv run coverage report
   ```

2. Write missing tests

3. Review coverage HTML report:
   ```bash
   uv run coverage html
   open htmlcov/index.html
   ```

### Test Failures

If tests fail:

1. Run tests locally:
   ```bash
   uv run python manage.py test
   ```

2. Fix errors

3. Commit and push

### Module-Specific Issues

If a specific module's tests fail:

```bash
# Run only that module's tests
uv run python manage.py test <module_name>

# With coverage
uv run coverage run --source='<module_name>' manage.py test <module_name>
uv run coverage report
```

## Best Practices

1. **Formatted code before every commit:** Run `uv format` before committing
2. **Run tests locally:** Make sure tests pass before pushing
3. **Track coverage:** Don't forget to write tests when writing new code
4. **Commit migration files:** Migration files are excluded from coverage
5. **Review CI logs:** Read detailed logs if pipeline fails
6. **Keep coverage high:** Aim to maintain or improve coverage percentages
7. **Test edge cases:** Write tests for both success and failure scenarios

## Coverage Targets Summary

| Module | Target | Reason |
|--------|--------|--------|
| auth | 85% | Critical security module |
| tenants | 80% | Multi-tenant architecture |
| users | 75% | Basic user management |
| employees | 80% | Business processes |
| titles | 95% | Simple CRUD operations |
| utils | 90% | Helper functions used everywhere |

## Pipeline Performance

- **Formatting Check:** ~30 seconds
- **Module Tests (Parallel):** ~3-5 minutes (longest job)
- **Total Pipeline Time:** ~4-6 minutes

## Useful Links

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Documentation](https://github.com/astral-sh/uv)
