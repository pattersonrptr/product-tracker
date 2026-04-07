# 🛒 Product Tracker

A price monitoring system that automatically tracks product prices across
multiple Brazilian e-commerce platforms (OLX, Mercado Livre, Enjoei, Estante
Virtual).

| Service | Tech | Directory |
|---|---|---|
| **Backend** | FastAPI · SQLAlchemy · Alembic · PostgreSQL | [`backend/`](backend/README.md) |
| **Scrapers** | Celery · BeautifulSoup · Cloudscraper · Redis | [`scrapers/`](scrapers/README.md) |
| **Frontend** | React 19 · Vite · MUI · TypeScript | [`frontend/`](frontend/README.md) |

---

## Quick Start

```bash
# Clone
git clone https://github.com/pattersonrptr/product-tracker.git
cd product-tracker

# Copy env file and adjust as needed
cp .env.example .env

# Start everything
make up

# Or without Make:
docker compose up --build
```

The services will be available at:

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost |
| Flower (Celery monitor) | http://localhost:5555 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## Development

```bash
# Run only infrastructure (db + redis)
make infra

# Backend dev server (outside Docker)
make backend-dev

# Frontend dev server (outside Docker)
make frontend-dev

# Run all tests
make test

# Run tests for a specific service
make backend-test
make scrapers-test
make frontend-test

# Lint
make lint
```

See the [`Makefile`](Makefile) for all available commands.

---

## Architecture

```
┌──────────┐       HTTP        ┌──────────┐       SQL        ┌──────────┐
│ Frontend │ ───────────────▶  │ Backend  │ ───────────────▶  │ Postgres │
│ (React)  │                   │ (FastAPI)│                   │          │
└──────────┘                   └────┬─────┘                   └──────────┘
                                    │ HTTP
                               ┌────┴─────┐
                               │ Scrapers │       broker      ┌──────────┐
                               │ (Celery) │ ◀───────────────  │  Redis   │
                               └──────────┘                   └──────────┘
```

- **Frontend** consumes the backend REST API (JSON:API spec).
- **Scrapers** are Celery workers that communicate with the backend
  exclusively via HTTP — no shared database access.
- **Backend** owns the database and exposes all data through the API.

---

## Project Structure

```
product-tracker/
├── backend/          ← FastAPI application + database
├── scrapers/         ← Celery workers + web scraping engines
├── frontend/         ← React SPA
├── docker-compose.yml
├── Makefile
├── .github/workflows/ci.yml
└── PLAN.md           ← Reorganization plan
```

---

## License

MIT
