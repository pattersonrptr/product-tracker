# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Playwright E2E test suite** — 74 tests (37 per browser × chromium + firefox)
  - Auth tests (11): login, logout, register, validation, auth guards
  - Alerts CRUD tests (7): create, edit, pause/resume, delete, modal cancel
  - Dashboard tests (3): cards display, alert count, navigation
  - Pages CRUD tests (16): products (edit, delete, filter), source websites CRUD, search configs CRUD, admin page smoke tests
  - Shared fixtures: `authenticatedPage`, `cleanupTestAlerts`, `cleanupTestWebsites`, `cleanupTestConfigs`
  - Playwright config with chromium + firefox, 10s timeout
- Root `package.json` with `@playwright/test` dependency

### Fixed

- **Frontend PATCH→PUT mismatch** — `sourceWebsiteService`, `searchConfigService`, `productService` used `apiClient.patch()` but backend expects `PUT` → 405 errors on edit
- **Products without prices** — `ProductRepository.get_all()` never joined `price_history`, returning `current_price: None` for all products; added LEFT JOIN to latest price subquery (same pattern as `search_by_term_and_sources`)
- **Products without prices (scraper side)** — `save_products` and `update_products` Celery tasks checked `product_data.get("current_price")` but scrapers return `price` field; now checks both field names
- **Dashboard "not yet triggered"** — `nextChecks` section used `alert.lastTriggeredAt` (only set on email notification), now uses `getExecutionStatus()` per search config for accurate last-run times
- **American date locale** — `formatDate`, `formatChartDateLabel`, `formatDateTime` changed from `en-US` to `pt-BR` locale
- **JWT token missing role claims** — added `is_staff` and `is_superuser` to JWT token payload in auth controller

### Changed

- `ProductRepository.get_by_id()` and `get_by_url()` now populate `current_price` from latest price history
- Dashboard service imports and uses `getExecutionStatus` from `searchConfigService` for next check computation
- Unit tests updated: formatter tests for pt-BR locale, dashboard service tests mock `getExecutionStatus`
- `.gitignore` updated with Playwright `test-results/` and `playwright-report/`
- Alerts E2E tests clean up search configs created as side effects (prevents pagination overflow)

---

- **Scraper closes the loop with alerts** (#38): per-product alert evaluation triggered immediately after each product is saved by the scraper
- `EvaluateProductAlertsUseCase` — evaluates all active `PriceAlert`s against a specific product, sends email notifications for matches and records `NotificationLog` entries
- `POST /products/{id}/evaluate-alerts` endpoint — replaces the old batch `send_price_alert_notifications` approach with per-product evaluation
- `PriceAlertRepository.find_matching_alerts_for_product()` — SQL JOIN on M2M source-website table + Python post-filter for case-insensitive keyword matching
- `NotificationLogRepository.exists_for_alert_and_product()` — dedup guard: skips notification if alert+product pair already has a successful log
- `ApiClient.evaluate_product_alerts(product_id)` — scraper-side HTTP call that triggers per-product evaluation after save
- Docker smoke test: `backend/src/scripts/api_tests/products/test_evaluate_alerts_smoke.sh`

### Changed

- `save_products` Celery task: calls `evaluate_product_alerts` per product immediately after create/update; removed the old batch `send_price_alert_notifications.apply_async` call

- **Dashboard + Alerts pages** (#37): user-facing frontend with dashboard summary and full PriceAlert CRUD
- `DashboardPage` with 3 summary cards — Active Alerts, Recent Opportunities, Next Checks
- `AlertsPage` with MUI DataGrid, create/edit modal, pause/resume toggle, single + bulk delete
- `priceAlertService` — full CRUD service for price alerts with JSON:API snake↔camelCase conversion
- `dashboardService` — client-side aggregation of alerts + matching products for dashboard summary
- `useDashboardSummary` React hook with loading/error state
- `types/priceAlert.ts` — PriceAlert, PriceAlertCreatePayload, PriceAlertUpdatePayload types
- `priceAlerts` endpoints in centralized endpoint definitions
- 🎯 Opportunity tag on ProductsPage — highlights products matching user's active alert max prices
- 12 unit tests for priceAlertService, 10 unit tests for dashboardService

### Changed

- Sidebar reorganized into User section (Dashboard, My Alerts, Products) and Admin section (Users, Search Configs, Source Websites) with divider
- Router rewritten — `/dashboard` as default landing, `/alerts` for alert management, admin routes under `/admin/*` with RequireAdmin guard
- Legacy routes (`/users`, `/search-configs`, `/source-websites`) redirect to `/admin/*` equivalents

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
