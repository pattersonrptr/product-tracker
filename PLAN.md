# 🏗️ Product Tracker — Monorepo Reorganization Plan

## Overview

This document describes the plan to consolidate the **Product Tracker** project
into a single monorepo with three top-level service directories (`backend/`,
`frontend/`, `scrapers/`) plus shared infrastructure at the root.

Previously the backend and frontend lived in separate Git repositories
(`product-tracker-backend` and `product-tracker-front`). The scraper workers
were embedded inside the backend under `src/product_scrapers/`.

### Goals

1. **Single repository** — one `.git`, one CI pipeline, unified tooling.
2. **Three independent services** — each with its own `Dockerfile`,
   dependencies, and README.
3. **Decoupled scrapers** — the Celery workers communicate with the backend
   exclusively via HTTP (no direct database imports).
4. **Root-level orchestration** — a single `docker-compose.yml` that brings up
   the entire stack (backend + scrapers + frontend + PostgreSQL + Redis).
5. **Shared config at the root** — `.gitignore`, `.pre-commit-config.yaml`,
   `.github/`, `Makefile`, and `.env.example`.

---

## Target Directory Structure

```
product-tracker/                  ← Git root
├── .git/
├── .github/
│   └── workflows/
│       └── ci.yml                ← unified CI (backend + scrapers + frontend)
├── .gitignore                    ← merged from both projects
├── .pre-commit-config.yaml       ← adapted for monorepo paths
├── .env.example                  ← combined env vars for all services
├── docker-compose.yml            ← full-stack orchestration
├── Makefile                      ← dev convenience commands
├── README.md                     ← project overview
├── LICENSE
├── PLAN.md                       ← this file
│
├── backend/                      ← FastAPI + SQLAlchemy + Alembic
│   ├── Dockerfile
│   ├── README.md
│   ├── pyproject.toml            ← no scraper deps (bs4, cloudscraper, celery…)
│   ├── poetry.lock
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── start.sh
│   ├── install_system_requirements.sh
│   ├── alembic/
│   └── src/
│       ├── __init__.py
│       ├── main.py
│       ├── app/                  ← domain, entities, use_cases, infra, interfaces
│       ├── common/
│       ├── config/
│       ├── scripts/
│       └── tests/                ← unit, integration, e2e (backend only)
│
├── scrapers/                     ← Celery workers + scraper engines
│   ├── Dockerfile
│   ├── README.md
│   ├── pyproject.toml            ← celery, requests, bs4, cloudscraper, redis, flower
│   ├── pytest.ini
│   └── src/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── api_client.py     ← HTTP client (talks to backend REST API)
│       ├── celery/
│       │   ├── __init__.py
│       │   ├── tasks.py
│       │   └── beat_schedule.py  ← refactored: uses ApiClient instead of DB
│       ├── scrapers/
│       │   ├── __init__.py
│       │   ├── interfaces/
│       │   ├── base/
│       │   ├── factory/
│       │   ├── manager/
│       │   ├── mixins/
│       │   ├── resources/
│       │   ├── olx.py
│       │   ├── enjoei.py
│       │   ├── mercado_livre.py
│       │   └── estante_virtual.py
│       └── tests/                ← scraper-specific tests
│           ├── api/
│           ├── celery/
│           └── scrapers/
│
└── frontend/                     ← React 19 + Vite + MUI
    ├── Dockerfile
    ├── README.md
    ├── nginx.conf
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    ├── eslint.config.js
    ├── index.html
    ├── public/
    └── src/
```

---

## Coupling Analysis — Why the Scrapers Can Be Extracted

| Component | Dependencies | Coupled to backend? |
|---|---|---|
| `scrapers/` (OLX, Enjoei …) | `requests`, `bs4`, `cloudscraper` + internal refs | ✅ No |
| `api/api_client.py` | `requests`, `os` (reads `API_URL`) | ✅ No — HTTP only |
| `celery/tasks.py` | `ApiClient`, `ScraperFactory`, `ScraperManager` | ✅ No — all internal |
| `celery/beat_schedule.py` | `src.app.infrastructure.database.*` | ❌ **YES** — direct DB |

**Only `beat_schedule.py`** imports from the backend codebase. Everything else
already communicates over HTTP through `ApiClient`.

### Decoupling Strategy — Option A: Beat via API

Replace the direct database query in `beat_schedule.py` with an HTTP call
through `ApiClient.get_active_search_configs()` (which already exists).

**Before (coupled):**
```python
from src.app.infrastructure.database.models.search_config_model import SearchConfig
from src.app.infrastructure.database_config import SessionLocal

db = SessionLocal()
searches = db.query(SearchConfig).filter(SearchConfig.is_active).all()
```

**After (decoupled):**
```python
from src.api.api_client import ApiClient

client = ApiClient(get_celery_worker_token())
searches = client.get_active_search_configs()
```

This eliminates the only import from `src.app` and makes the scrapers service
fully independent.

---

## Execution Steps

### Phase 1 — Move & Rename

| # | Task | Details |
|---|---|---|
| 1 | Rename directories | `product-tracker-backend/` → `backend/`, `product-tracker-front/` → `frontend/` |
| 2 | Extract scrapers | Move `backend/src/product_scrapers/` → `scrapers/src/` |
| 3 | Move scraper tests | Move `backend/src/tests/product_scrapers/` → `scrapers/src/tests/` |
| 4 | Move `.github/` to root | From `backend/.github/` → `.github/` |
| 5 | Move `.pre-commit-config.yaml` to root | From `backend/` → root |
| 6 | Remove old docker-compose files | Delete `backend/docker-compose.yml` and `frontend/docker-compose.yml` |

### Phase 2 — Decouple & Configure

| # | Task | Details |
|---|---|---|
| 7 | Refactor `beat_schedule.py` | Replace direct DB access with `ApiClient` HTTP calls |
| 8 | Fix scraper imports | Change `src.product_scrapers.*` → `src.*` (new package root) |
| 9 | Create `scrapers/pyproject.toml` | Deps: `celery`, `flower`, `redis`, `requests`, `beautifulsoup4`, `cloudscraper`, `python-dotenv` |
| 10 | Create `scrapers/Dockerfile` | Lightweight image, no DB drivers needed |
| 11 | Clean backend `pyproject.toml` | Remove: `beautifulsoup4`, `cloudscraper`, `celery`, `flower`, `redis` |
| 12 | Update Celery task names | Change `src.product_scrapers.celery.tasks.*` → `src.celery.tasks.*` |

### Phase 3 — Root-Level Infrastructure

| # | Task | Details |
|---|---|---|
| 13 | Create unified `.gitignore` | Merge Python + Node.js ignores |
| 14 | Create root `docker-compose.yml` | All services: `web`, `scraper`, `celery-beat`, `flower`, `db`, `redis`, `frontend` |
| 15 | Create root `.env.example` | Combined variables for all services |
| 16 | Create root `README.md` | Project overview pointing to sub-READMEs |
| 17 | Create `scrapers/README.md` | Documentation for the scrapers service |
| 18 | Create `Makefile` | Shortcuts: `make up`, `make backend-test`, `make scrapers-test`, `make frontend-dev`, etc. |
| 19 | Update `.pre-commit-config.yaml` | Adjust paths for monorepo layout |
| 20 | Update `.github/workflows/ci.yml` | Add jobs for backend, scrapers, and frontend with `working-directory` |

### Phase 4 — Validate

| # | Task | Details |
|---|---|---|
| 21 | Verify directory structure | Ensure no broken references or leftover files |
| 22 | Run backend tests | `cd backend && poetry run pytest` |
| 23 | Run scraper tests | `cd scrapers && poetry run pytest` |
| 24 | Run frontend tests | `cd frontend && npm test` |
| 25 | Test docker-compose | `docker compose up --build` from root |

---

## Dependency Split

### Backend `pyproject.toml` (keeps)

```
fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, pydantic,
python-jose, passlib, bcrypt, python-dotenv, python-multipart,
email-validator
```

### Scrapers `pyproject.toml` (new)

```
celery, flower, redis, requests, beautifulsoup4, cloudscraper,
python-dotenv
```

### Frontend `package.json` (unchanged)

```
react, react-dom, react-router-dom, axios, @mui/material,
@mui/x-data-grid, recharts, notistack, jwt-decode
```

---

## Docker Compose — Service Topology

```
┌─────────────────────────────────────────────────────────┐
│                   docker-compose.yml                     │
│                                                          │
│  ┌─────────┐  ┌─────────┐  ┌────────────┐  ┌─────────┐ │
│  │   web   │  │ scraper │  │ celery-beat│  │ flower  │ │
│  │ (back.) │  │ (scrap.)│  │  (scrap.)  │  │ (scrap.)│ │
│  └────┬────┘  └────┬────┘  └─────┬──────┘  └────┬────┘ │
│       │            │              │               │      │
│       ▼            ▼              ▼               ▼      │
│  ┌─────────┐  ┌─────────┐                               │
│  │   db    │  │  redis  │                               │
│  │ (pg13) │  │ (alpine)│                               │
│  └─────────┘  └─────────┘                               │
│                                                          │
│  ┌──────────┐                                            │
│  │ frontend │                                            │
│  │ (nginx)  │                                            │
│  └──────────┘                                            │
└─────────────────────────────────────────────────────────┘
```

Communication:
- **scraper / celery-beat → web**: HTTP (`API_URL=http://web:8000`)
- **scraper / celery-beat → redis**: Celery broker
- **web → db**: PostgreSQL
- **frontend → web**: HTTP (proxied via nginx or env-configured)
- **flower → redis**: Celery monitoring

---

## Known Issues & Next Steps

### Scrapers

| # | Issue | Severity | Details |
|---|---|---|---|
| 1 | **OLX blocked in Docker** | 🔴 High | OLX blocks datacenter IPs — scraper returns 0 results from Docker containers. Works locally. Needs proxy rotation or residential IP solution. |
| 2 | **`process_urls_list` RuntimeError** | 🟡 Medium | Calling `chord(group(...), callback)` inside a Celery task triggers `RuntimeError: Never call result.get() within a task`. Needs refactoring to avoid the chord anti-pattern (e.g., use `chain` + `on_chord_error` or replace with sequential processing). |
| 3 | **422 on `/products/by-url`** | 🟡 Medium | Backend endpoint returns 422 for some product URLs during `save_product`. Likely a validation issue on `ProductCreatePayload`. Needs investigation. |
| 4 | **Mercado Livre partial scrape rate** | 🟢 Low | ML search finds ~279 URLs but only ~54 products are successfully scraped (19% success). Many product pages may have changed layout or are no longer available. |

### Frontend

| # | Issue | Details |
|---|---|---|
| 5 | **No UI trigger for scraping** | There is no button or page in the frontend to manually start a scraper task. Users must invoke tasks via `docker compose exec` or Flower. |

### Infrastructure

| # | Issue | Details |
|---|---|---|
| 6 | **`.env` not in repo** | Root `.env` with secrets is `.gitignore`d. Need to create `.env.example` with placeholder values for onboarding. |
| 7 | **No health checks in compose** | Services don't have Docker `healthcheck` directives — `depends_on` doesn't wait for readiness. |

---

## Notes

- The scrapers service has **no database driver** — it never talks to
  PostgreSQL directly.
- Each service can be built and tested independently.
- The `Makefile` provides a unified developer experience despite the split.
- Future scrapers (new e-commerce sites) are added only in `scrapers/` — no
  changes needed in `backend/` or `frontend/`.
