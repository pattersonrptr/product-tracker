# Poetry Migration Guide

This project now uses Poetry for dependency management alongside the traditional `requirements.txt`.

## Why Poetry?

- **Better dependency resolution**: Handles conflicts automatically
- **Lock file**: Reproducible builds with `poetry.lock`
- **Dev dependencies**: Separate production and development packages
- **Virtual environment management**: Automatic venv handling
- **Modern tooling**: Industry standard for Python projects

## Installation

Poetry is already configured in this project. If you need to install it system-wide:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

## Usage

### Installing Dependencies

```bash
# Install all dependencies (production + dev)
poetry install

# Install only production dependencies
poetry install --only main
```

### Running Commands

```bash
# Run tests
poetry run pytest

# Run the application
poetry run python -m src.main

# Run pre-commit hooks
poetry run pre-commit run --all-files

# Run Ruff
poetry run ruff check src/

# Run MyPy
poetry run mypy src/
```

### Adding Dependencies

```bash
# Add production dependency
poetry add fastapi

# Add dev dependency
poetry add --group dev pytest

# Add with version constraint
poetry add "requests>=2.28,<3.0"
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update specific package
poetry update fastapi

# Show outdated packages
poetry show --outdated
```

### Exporting Requirements

```bash
# Export to requirements.txt (for Docker, etc)
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Export dev dependencies too
poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes
```

## Migration from requirements.txt

The project still maintains `requirements.txt` for backward compatibility, but **Poetry is the source of truth** for dependencies.

To sync `requirements.txt` with Poetry:

```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Virtual Environment

Poetry automatically creates and manages a virtual environment:

```bash
# Show venv info
poetry env info

# Activate venv (not usually needed, use `poetry run` instead)
poetry shell

# List all venvs
poetry env list

# Remove venv
poetry env remove python
```

## Docker Integration

For Docker builds, you can still use `requirements.txt`:

```dockerfile
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install -r requirements.txt
```

Or install with Poetry directly:

```dockerfile
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Install Poetry
  run: pipx install poetry

- name: Install dependencies
  run: poetry install

- name: Run tests
  run: poetry run pytest
```

## Common Issues

### Cache Issues

```bash
poetry cache clear pypi --all
poetry install
```

### Lock File Out of Sync

```bash
poetry lock --no-update
```

### Python Version Mismatch

Make sure your Python version matches `pyproject.toml`:

```bash
poetry env use python3.11
```

## References

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry Commands](https://python-poetry.org/docs/cli/)
- [pyproject.toml spec](https://python-poetry.org/docs/pyproject/)
