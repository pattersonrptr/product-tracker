FROM python:3.11-slim

WORKDIR /src

# System dependencies (includes libs required by Playwright/Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libx11-xcb1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Configure Poetry: no venv inside container, no interaction
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Copy dependency files first (layer cache optimisation)
COPY pyproject.toml poetry.lock ./

# Install dependencies
ARG BUILD_ENV=prod
RUN if [ "$BUILD_ENV" = "dev" ]; then \
        poetry install --no-root; \
    else \
        poetry install --only main --no-root; \
    fi

# Install Playwright Chromium browser binary
RUN playwright install chromium

COPY . .

# Default: run Celery worker (overridden in docker-compose per service)
CMD ["celery", "-A", "src.celery.tasks", "worker", "--loglevel=info"]
