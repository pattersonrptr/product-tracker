# Product Tracker — Project Status

> **Garimpei** (nome de produto) · `product-tracker` (nome de desenvolvimento)
>
> Roadmap completo: [ROADMAP.md](./ROADMAP.md)

---

## Architecture

Monorepo with 3 independent services orchestrated by Docker Compose:

```
product-tracker/
├── backend/    → FastAPI + SQLAlchemy + Alembic + PostgreSQL
├── scrapers/   → Celery + Playwright + BeautifulSoup + Redis
├── frontend/   → React 19 + Vite + MUI + TypeScript
└── docker-compose.yml
```

**Key rule:** Scrapers communicate with the backend **exclusively via HTTP**
(no direct database access). All communication flows through the JSON:API.

## Current Capabilities

### Backend (FastAPI)

- JWT authentication with token refresh
- User roles (admin, staff, regular)
- CRUD for: Products, Price History, Source Websites, Search Configs, Search Execution Logs
- JSON:API compliant responses
- 486+ tests passing

### Scrapers (Celery)

- 4 platforms: OLX, Mercado Livre, Enjoei, Estante Virtual
- Celery Beat dynamic scheduler (syncs search configs from API)
- Playwright-based scraping (all 4 scrapers)
- ML rate-limiting: 15s search delay, 10s product delay, shuffle, context rotation
- Proxy infrastructure ready (paid + free rotation with fallback)
- 291+ tests passing

### Frontend (React)

- Product listing with pagination, sorting, filters
- Price history charts (Recharts)
- Search config management (CRUD)
- Source website management
- User management
- JWT auth with interceptors

### Infrastructure

- Docker Compose: web, scraper, celery-beat, flower, db, redis, frontend
- GitHub Actions CI: lint + format + tests for all 3 services
- Pre-commit hooks configured

## Quick Reference

```bash
make up          # Start all services
make down        # Stop everything
make test        # Run all tests
make lint        # Lint all services
```

| Service  | URL                        |
|----------|----------------------------|
| API      | http://localhost:8000       |
| Frontend | http://localhost            |
| Flower   | http://localhost:5555       |
| Swagger  | http://localhost:8000/docs  |

## Known Issues

| # | Issue | Severity | Details |
|---|-------|----------|---------|
| 1 | OLX blocked in Docker | 🟡 Medium | OLX blocks some datacenter IPs. Works locally. Proxy rotation mitigates. |
| 2 | No health checks in compose | 🟢 Low | Services don't have Docker `healthcheck` directives. |

## Next Steps

See **[ROADMAP.md](./ROADMAP.md)** for the full Garimpei product roadmap.

**Immediate priority:** Fase 1 — Price Alerts + Email Notifications + Dashboard.