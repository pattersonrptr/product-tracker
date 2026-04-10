# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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
