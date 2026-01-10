# Atlas Data Pipeline Platform - Development Workflow Guide

**Version:** 1.0
**Last Updated:** January 2026

This guide outlines the development workflow, branching strategy, code review process, and deployment procedures for the Atlas Data Pipeline Platform.

## Table of Contents

- [Development Environment](#development-environment)
- [Git Workflow](#git-workflow)
- [Branching Strategy](#branching-strategy)
- [Code Review Process](#code-review-process)
- [Testing Strategy](#testing-strategy)
- [Deployment Process](#deployment-process)
- [Release Management](#release-management)

## Development Environment

### Local Development Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url> atlas-pipeline
   cd atlas-pipeline
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Using uv (recommended)
   pip install uv
   uv pip install -e ".[dev]"

   # Or using pip
   pip install -e ".[dev]"
   ```

4. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   pre-commit run --all-files  # Test hooks
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

6. **Start Services**
   ```bash
   docker-compose up -d
   ```

7. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

8. **Create Initial Data**
   ```bash
   python -m app.initial_data
   ```

### Development Tools

**Required**:
- Python 3.11+
- Docker & Docker Compose
- Git
- IDE (VS Code, PyCharm, etc.)

**Recommended VS Code Extensions**:
- Python
- Pylance
- Black Formatter
- isort
- Ruff
- Docker
- GitLens
- REST Client

**Recommended Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.rulers": [100]
  }
}
```

## Git Workflow

### Repository Structure

```
atlas-pipeline/
├── .git/              # Git repository
├── .github/           # GitHub Actions workflows
├── app/               # Application code
├── tests/             # Test suite
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── examples/          # Integration examples
└── ...
```

### Commit Message Format

Follow conventional commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes
- `perf`: Performance improvements

**Examples**:
```bash
feat(pipeline): add PII detection to bronze layer

Implemented Presidio integration for automatic PII detection
during bronze layer ingestion. Supports 20+ entity types.

Closes #123

fix(api): correct pagination offset calculation

The offset was incorrectly calculated causing duplicate results
on page boundaries.

docs(readme): update setup instructions

Added troubleshooting section and Docker version requirements.

test(quality): add soda core integration tests
```

### Commit Best Practices

1. **Atomic Commits**: One logical change per commit
2. **Clear Messages**: Descriptive and concise
3. **Reference Issues**: Link to issue tracker
4. **Sign Commits**: Use GPG signing (optional but recommended)

```bash
# Sign a commit
git commit -S -m "feat: add new feature"

# Set up GPG signing globally
git config --global commit.gpgsign true
```

## Branching Strategy

### Branch Types

```
main
├── develop
│   ├── feature/add-pii-detection
│   ├── feature/improve-quality-checks
│   ├── bugfix/fix-pagination
│   ├── hotfix/critical-security-patch
│   └── release/v1.1.0
```

### Branch Naming Conventions

| Type | Pattern | Example | Purpose |
|------|---------|---------|---------|
| Feature | `feature/<description>` | `feature/add-pii-detection` | New features |
| Bugfix | `bugfix/<description>` | `bugfix/fix-pagination` | Non-critical fixes |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` | Critical production fixes |
| Release | `release/v<version>` | `release/v1.1.0` | Release preparation |
| Experiment | `experiment/<description>` | `experiment/new-algorithm` | Experimental work |

### Branch Workflow

#### Feature Development

```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/add-pii-detection

# 3. Develop and commit
git add .
git commit -m "feat(pii): add presidio integration"

# 4. Push to remote
git push -u origin feature/add-pii-detection

# 5. Create Pull Request
# Via GitHub UI or gh CLI
gh pr create --base develop --title "Add PII detection"

# 6. After review and approval
# Merge via GitHub (squash and merge recommended)

# 7. Clean up
git checkout develop
git pull origin develop
git branch -d feature/add-pii-detection
```

#### Bugfix

```bash
# Similar to feature, but from develop
git checkout develop
git checkout -b bugfix/fix-pagination
# ... develop, commit, push, PR
```

#### Hotfix (Production)

```bash
# 1. Start from main
git checkout main
git pull origin main

# 2. Create hotfix branch
git checkout -b hotfix/security-patch

# 3. Fix and commit
git commit -m "fix(security): patch SQL injection vulnerability"

# 4. Push and create PR to main
git push -u origin hotfix/security-patch

# 5. After merge to main, also merge to develop
git checkout develop
git merge main
git push origin develop

# 6. Tag release
git checkout main
git tag -a v1.0.1 -m "Hotfix: Security patch"
git push origin v1.0.1
```

### Branch Protection Rules

**`main` branch**:
- Require pull request reviews (2 approvals)
- Require status checks to pass
- Require branches to be up to date
- Require signed commits
- No direct pushes
- No force pushes

**`develop` branch**:
- Require pull request reviews (1 approval)
- Require status checks to pass
- Allow force push for maintainers only

## Code Review Process

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests passing

## Quality Checks
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated

## Related Issues
Closes #123

## Screenshots (if applicable)
```

### Review Checklist

**For Authors**:
1. Self-review your changes
2. Ensure all tests pass
3. Update documentation
4. Add/update comments
5. Check code style compliance
6. Rebase on target branch
7. Fill out PR template completely

**For Reviewers**:
1. Understand the context and requirements
2. Check code logic and correctness
3. Verify test coverage
4. Review error handling
5. Check for security issues
6. Verify documentation updates
7. Test locally if needed
8. Provide constructive feedback

### Review Labels

- `needs-review`: Awaiting initial review
- `changes-requested`: Reviewer requested changes
- `approved`: Review approved
- `blocked`: Blocked by external dependency
- `wip`: Work in progress, not ready for review

### Review Best Practices

**As Author**:
- Keep PRs small and focused (<300 lines)
- Provide context and rationale
- Respond to feedback promptly
- Test thoroughly before requesting review

**As Reviewer**:
- Be respectful and constructive
- Ask questions instead of making demands
- Suggest alternatives with reasoning
- Approve when satisfied, don't nitpick

## Testing Strategy

### Test Pyramid

```
           ┌─────────────┐
           │   E2E (5%)  │  Full pipeline integration
           ├─────────────┤
           │Integration  │  Component interactions
           │   (20%)     │
           ├─────────────┤
           │   Unit      │  Individual functions/classes
           │   (75%)     │
           └─────────────┘
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_pipeline.py

# Specific test function
pytest tests/test_pipeline.py::test_bronze_to_silver

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run in parallel
pytest -n auto
```

### Test Structure

```python
# tests/test_pipeline.py
import pytest
from app.pipeline.core import Pipeline

@pytest.mark.unit
def test_pipeline_initialization():
    """Test pipeline initialization with valid config."""
    pipeline = Pipeline(name="test_pipeline")
    assert pipeline.name == "test_pipeline"
    assert pipeline.status == "initialized"

@pytest.mark.integration
async def test_bronze_to_silver_transformation(db_session, sample_data):
    """Test full bronze to silver transformation."""
    # Arrange
    await ingest_to_bronze(sample_data)

    # Act
    result = await transform_bronze_to_silver()

    # Assert
    assert result.records_processed == 100
    assert result.quality_score > 0.95
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    engine = create_engine("postgresql://test:test@localhost/test_db")
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Create test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
    ]
```

### Coverage Requirements

- Minimum overall coverage: 80%
- Minimum new code coverage: 90%
- Critical paths: 100% coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Deployment Process

### Environments

| Environment | Purpose | Branch | Deployment |
|-------------|---------|--------|------------|
| Development | Local development | Any | Manual |
| Testing | Integration testing | `develop` | Auto (on push) |
| Staging | Pre-production | `release/*` | Auto (on push) |
| Production | Live system | `main` | Manual (approval) |

### Deployment Workflow

#### To Testing Environment

```bash
# Automatic on push to develop
git push origin develop

# GitHub Actions workflow:
# 1. Run tests
# 2. Build Docker images
# 3. Deploy to testing environment
# 4. Run smoke tests
```

#### To Staging Environment

```bash
# Create release branch
git checkout -b release/v1.1.0 develop

# Update version
# Edit pyproject.toml: version = "1.1.0"
git commit -am "chore: bump version to 1.1.0"

# Push to remote
git push origin release/v1.1.0

# Automatic deployment to staging
```

#### To Production

```bash
# 1. Merge release to main
gh pr create --base main --title "Release v1.1.0"

# 2. After approval and merge, tag release
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release v1.1.0: Add PII detection"
git push origin v1.1.0

# 3. Manual deployment approval required
# Via GitHub Actions UI

# 4. Merge back to develop
git checkout develop
git merge main
git push origin develop
```

### Pre-deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Database migrations tested
- [ ] Backup completed
- [ ] Rollback plan prepared

### Post-deployment Tasks

1. Verify deployment success
2. Run smoke tests
3. Monitor logs and metrics
4. Check error rates
5. Notify team
6. Update project management tools

## Release Management

### Versioning

Follow Semantic Versioning (SemVer):

```
MAJOR.MINOR.PATCH

1.0.0 → Initial release
1.1.0 → New feature (backward compatible)
1.1.1 → Bug fix
2.0.0 → Breaking change
```

### Release Process

1. **Create Release Branch**
   ```bash
   git checkout -b release/v1.1.0 develop
   ```

2. **Update Version and Changelog**
   ```bash
   # Edit pyproject.toml
   # Edit CHANGELOG.md
   git commit -am "chore: prepare release v1.1.0"
   ```

3. **Test Release Candidate**
   ```bash
   # Deploy to staging
   # Run full test suite
   # Perform manual testing
   ```

4. **Merge to Main**
   ```bash
   git checkout main
   git merge release/v1.1.0
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin main --tags
   ```

5. **Deploy to Production**
   ```bash
   # Via GitHub Actions with manual approval
   ```

6. **Merge Back to Develop**
   ```bash
   git checkout develop
   git merge main
   git push origin develop
   ```

7. **Create GitHub Release**
   ```bash
   gh release create v1.1.0 --title "v1.1.0" --notes-file RELEASE_NOTES.md
   ```

### CHANGELOG.md Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-01-15

### Added
- PII detection with Microsoft Presidio
- Data quality validation with Soda Core
- Data lineage tracking with OpenLineage

### Changed
- Improved pipeline performance by 30%
- Updated FastAPI to 0.109.0

### Fixed
- Fixed pagination bug in API
- Corrected PII detection for Danish text

### Security
- Patched SQL injection vulnerability

## [1.0.0] - 2026-01-01

### Added
- Initial release
- Medallion architecture (Bronze/Silver/Gold)
- FastAPI REST API
- Basic pipeline orchestration
```

### Release Notes Template

```markdown
# Release v1.1.0

## Overview
This release adds comprehensive PII detection and data quality validation capabilities to the Atlas Data Pipeline Platform.

## New Features
- **PII Detection**: Automatic detection and anonymization using Microsoft Presidio
- **Data Quality**: 6-dimension quality framework with Soda Core
- **Lineage Tracking**: Full data lineage with OpenLineage integration

## Improvements
- 30% faster pipeline execution
- Enhanced error handling
- Improved documentation

## Bug Fixes
- Fixed pagination issue in API (#123)
- Corrected PII detection for non-English text (#145)

## Breaking Changes
None

## Migration Guide
No breaking changes. Simply update to v1.1.0.

## Known Issues
- Dashboard UI is still in beta
- Bot integration is optional

## Contributors
@developer1, @developer2, @developer3
```

---

**Atlas Data Pipeline Platform** - Professional development workflow for production-grade systems

**Next Steps**:
- Read [Setup Guide](SETUP.md) for environment configuration
- Review [Architecture Guide](ARCHITECTURE.md) for system design
- Check [API Reference](API.md) for endpoint documentation
