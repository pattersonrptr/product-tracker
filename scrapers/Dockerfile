FROM python:3.11-slim

WORKDIR /src

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Configure Poetry: no venv inside container, no interaction
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Copy dependency files first (layer cache optimisation)
COPY pyproject.toml ./

# Install dependencies
ARG BUILD_ENV=prod
RUN if [ "$BUILD_ENV" = "dev" ]; then \
        poetry install --no-root; \
    else \
        poetry install --only main --no-root; \
    fi

COPY . .

# Default: run Celery worker (overridden in docker-compose per service)
CMD ["celery", "-A", "src.celery.tasks", "worker", "--loglevel=info"]
