# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Email notifications via SendGrid** (#36): send email alerts when products matching a PriceAlert are found below the target price
- `NotificationLog` entity, SQLAlchemy model, repository interface + implementation
- `SendPriceAlertNotificationUseCase` with configurable rate limiting (default 1 email/alert/hour)
- `EmailServiceInterface` (ABC) + `SendGridEmailService` implementation
- `build_price_alert_email` helper — HTML email with product listing, prices in R$, source names
- `POST /price-alerts/{id}/notify` endpoint to trigger notification check for a specific alert
- `GET /notification-logs` CRUD endpoints (list, get by id, by alert, by user, delete) — staff-only
- Alembic migration `003_add_notification_logs` with indexes on `price_alert_id`, `user_id`, `sent_at`
- `send_price_alert_notifications` Celery task — triggered after `save_products` with 5s countdown
- `trigger_notifications` + `trigger_price_alert_notification` methods on scrapers `ApiClient`
- `SENDGRID_API_KEY`, `NOTIFICATION_FROM_EMAIL`, `NOTIFICATION_RATE_LIMIT_MINUTES` env vars
- 28 unit tests for notification use cases (send, rate limit, CRUD)
- 8 unit tests for notification log presenter
- 4 unit tests for `send_price_alert_notifications` Celery task
- **Link SearchConfig → PriceAlert** (#35): auto-create/reuse SearchConfig when a PriceAlert is created, cleanup orphaned SearchConfigs on deactivation/deletion
- `search_config_id` FK column on `price_alerts` table (nullable) with index
- `GET /price-alerts/{id}/products` endpoint — search products matching an alert's term, sources, and optional max_price filter
- `search_by_term_and_sources` method on ProductRepository (ILIKE + latest price subquery)
- `count_active_by_search_config_id` method on PriceAlertRepository
- `GetProductsByPriceAlertUseCase` with pagination support
- Alembic migration `002_add_search_config_id_to_price_alerts`
- 32 unit tests for SearchConfig linking, orphan cleanup, and product search use cases
- **PriceAlert entity + full CRUD** (#34): domain entity, SQLAlchemy model, M2M association table (alert↔source_websites), repository interface + implementation, use cases (Create, GetById, GetByUserId, List, Update, Delete), JSON:API schemas, presenter, validator, controller with all REST endpoints (`/price-alerts`)
- Alembic migration for `price_alerts` and `price_alert_source_website` tables
- 37 unit tests (use cases, presenter, validator)
- Product roadmap for Garimpei — `ROADMAP.md` with 4 phases
- Frontend assessment documenting keep-and-evolve strategy
- GitHub milestones (Phase 1–3) and issues (#34–#46) with checklists
- Labels: `backend`, `frontend`, `scrapers`, `infra`
- Copilot instructions with SemVer, conventional commits, and release process

### Changed

- Rewrote `PLAN.md` as clean project status document (removed outdated monorepo reorganization content)

### Removed

- Experiment files: `ml_threshold_experiment.py`, `ml_ip_monitor.py`, `test_scrapers_live.py`, etc.
- `QWEN.md` (outdated AI conversation notes)
- Conversation file with Claude Sonnet (not tracked)

---

## [0.0.0] — 2025-06-01

### Added

- **Backend:** FastAPI + SQLAlchemy + Alembic + PostgreSQL
  - JWT auth with refresh tokens, user roles (admin, staff, regular)
  - Full CRUD: Products, Price History, Source Websites, Search Configs, Execution Logs
  - JSON:API compliant responses, 486+ tests
- **Scrapers:** Celery + Playwright + BeautifulSoup + Redis
  - 4 platforms: OLX, Mercado Livre, Enjoei, Estante Virtual
  - Celery Beat dynamic scheduler (syncs configs via API)
  - ML rate-limiting validated (492/492, zero blocks)
  - Proxy infrastructure (paid + free rotation with fallback), 291+ tests
- **Frontend:** React 19 + Vite + MUI + TypeScript
  - Product listing with pagination, filters, sorting
  - Price history charts (Recharts)
  - Search config CRUD, source website CRUD, user management
  - JWT auth with interceptors
- **Infrastructure:** Docker Compose, GitHub Actions CI, pre-commit hooks
