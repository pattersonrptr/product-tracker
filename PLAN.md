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
- **PriceAlert CRUD** (`/price-alerts`) — keyword + max price + source websites, M2M association
- **SearchConfig ↔ PriceAlert linking** — auto-create/reuse on alert creation, orphan cleanup
- **NotificationLog + SendGrid email notifications** — rate-limited (1/alert/hour), HTML templates
- `GET /price-alerts/{id}/products` — products matching alert term + sources + max_price
- `POST /price-alerts/{id}/notify` — trigger notification check for a specific alert
- **`POST /products/{id}/evaluate-alerts`** — per-product alert evaluation with dedup guard
- `EvaluateProductAlertsUseCase` — matches active alerts by keyword + source + price, sends emails, prevents duplicate notifications via `NotificationLog`
- JSON:API compliant responses
- Product repository with latest price JOIN (current_price from price_history)
- JWT tokens include `is_staff` and `is_superuser` claims
- 585+ tests passing

### Scrapers (Celery)

- 4 platforms: OLX, Mercado Livre, Enjoei, Estante Virtual
- Celery Beat dynamic scheduler (syncs search configs from API)
- Playwright-based scraping (all 4 scrapers)
- **Per-product notification trigger** — `evaluate_product_alerts` called after each product save (replaces old batch approach)
- ML rate-limiting: 15s search delay, 10s product delay, shuffle, context rotation
- Proxy infrastructure ready (paid + free rotation with fallback)
- Price field normalization: accepts both `price` and `current_price` from scraper data
- 339+ tests passing

### Frontend (React)

- **Dashboard page** (`/dashboard`) — Active Alerts, Recent Opportunities, Next Checks cards
- **My Alerts page** (`/alerts`) — PriceAlert CRUD with DataGrid, create/edit modal, pause/resume
- Product listing with pagination, sorting, filters + **🎯 Opportunity tag**
- Price history charts (Recharts)
- **Sidebar reorganized** — User section + Admin section with RequireAdmin route guard
- Search config management (admin), Source website management (admin), User management (admin)
- Date/currency formatting in pt-BR locale
- JWT auth with interceptors
- 61 unit tests (Vitest) + 74 E2E tests (Playwright: chromium + firefox)
- E2E coverage: auth flows, alerts CRUD, dashboard, products, source websites CRUD, search configs CRUD

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
| 3 | Frontend not volume-mounted | 🟢 Low | Frontend Docker container requires `docker compose build frontend` after code changes (unlike backend/scrapers which are volume-mounted). |

## Next Steps

See **[ROADMAP.md](./ROADMAP.md)** for the full Garimpei product roadmap.

**Phase 1 — Core is COMPLETE** ✅ (Issues #34, #35, #36, #37)

**Next priority:** Phase 2 — Polish (landing page, new scrapers, admin dashboard).

## Planned Improvements

### ✅ Playwright E2E Tests (End-to-End) — DONE

Browser-based E2E tests using Playwright Test (TypeScript) that validate the
full stack: Browser → Frontend → API → Database.

**74 tests** (37 × 2 browsers: chromium + firefox):

- Auth: login, logout, register, validation, guards (11 tests)
- Alerts: full CRUD, pause/resume, modal cancel (7 tests)
- Dashboard: cards, counts, navigation (3 tests)
- Pages: products edit/delete, source websites CRUD, search configs CRUD, admin smoke (16 tests)

Run with `cd frontend && npx playwright test`.

### Separate Test Database

Use a dedicated test database (`product_tracker_test`) so that:

- Dev/user data in `product_tracker` is never affected by tests
- Tests that need a database (integration, e2e) use their own isolated DB
- Works both locally (bare metal) and via Docker Compose
- Test DB is created/destroyed automatically by the test runner

**Implementation ideas:**

- Backend: override `DATABASE_URL` in test fixtures (pytest `conftest.py`)
- Docker: add a `db-test` service or use `docker compose --profile test`
- Alembic migrations run against test DB before test suite
