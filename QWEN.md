# Product Tracker - QWEN.md

## Overview

**Product Tracker** is a price monitoring system that automatically tracks products across 4 Brazilian e-commerce platforms: **OLX, Mercado Livre, Enjoei, and Estante Virtual**.

It is a **monorepo** with 3 independent services orchestrated by Docker Compose:
- **Backend** (FastAPI + PostgreSQL) — REST API following JSON:API spec
- **Scrapers** (Celery + Redis) — Async scraping workers
- **Frontend** (React + MUI) — SPA with tables, charts, and JWT authentication

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 13, JWT, Poetry, pytest (486 tests), Ruff, MyPy, Bandit |
| **Scrapers** | Celery 5.5, Redis, Requests, Cloudscraper, BeautifulSoup4, Playwright, Ruff |
| **Frontend** | React 19, TypeScript 5.9, Vite 7, MUI v6, React Router v7, Axios (JWT interceptor), Recharts, Vitest, ESLint |
| **Infra** | Docker Compose, GitHub Actions CI, Pre-commit hooks |

## Project Structure

```
product-tracker/
├── backend/src/
│   ├── app/
│   │   ├── entities/           ← Domain entities (User, Product, PriceHistory...)
│   │   ├── use_cases/          ← Business rules (CRUD per domain)
│   │   ├── domain/validators/  ← Business rule validations
│   │   ├── infrastructure/     ← SQLAlchemy repositories, ORM models
│   │   ├── interfaces/http/    ← Controllers, Pydantic schemas, JSON:API presenters
│   │   └── security/           ← JWT auth
│   ├── config/                 ← Settings and logging
│   ├── common/                 ← Shared utilities
│   ├── scripts/                ← create_superuser, init_dev_db
│   └── tests/                  ← Unit, Integration, E2E
├── scrapers/src/
│   ├── api/api_client.py       ← HTTP client for backend API (JSON:API)
│   ├── celery/
│   │   ├── tasks.py            ← 8 Celery tasks
│   │   └── beat_schedule.py    ← DynamicScheduler
│   └── scrapers/
│       ├── factory/            ← ScraperFactory
│       ├── manager/            ← ScraperManager
│       ├── olx.py, enjoei.py, mercado_livre.py, estante_virtual.py
│       └── base/, mixins/, interfaces/
├── frontend/src/
│   ├── api/                    ← Axios client with JWT interceptors
│   ├── services/               ← 6 services (auth, user, product...)
│   ├── hooks/                  ← usePaginatedResource, useProductDetails
│   ├── context/                ← AuthContext
│   ├── components/             ← Common + Layout
│   ├── pages/                  ← 7 pages (Login, Products, Users...)
│   └── router/                 ← Routes + RequireAuth guard
├── docker-compose.yml          ← Topology: web, scraper, celery-beat, flower, db, redis, frontend
├── Makefile                    ← Main commands
└── .github/workflows/ci.yml    ← CI with 3 independent jobs
```

## Communication Flow

```
Frontend (:80) --HTTP--> Backend (:8000) --SQL--> PostgreSQL
Scrapers --HTTP--> Backend (read/write data via JSON:API)
Scrapers/Celery-beat --Redis--> Redis (broker)
Flower --Redis--> Redis (monitoring)
```

**Important rule:** Scrapers communicate with the backend **exclusively via HTTP** — never access the database directly.

## Development Commands

```bash
# Start everything
make up                          # docker compose up --build -d
make down                        # stop everything
make logs                        # tail logs

# Local development
make backend-dev                 # uvicorn --reload
make frontend-dev                # vite dev

# Tests (minimum 60% coverage on CI)
make test                        # all tests
make backend-test                # pytest src/tests/ -v
make scrapers-test               # pytest src/tests/ -v
make frontend-test               # vitest

# Lint & Type Check
make lint                        # all lints
make backend-lint                # ruff check + format
make scrapers-lint               # ruff check + format
make frontend-lint               # eslint

# Docker
make infra                       # db + redis only
make build                       # build images
make backend-shell               # bash in web container
```

## Known Issues (see PLAN.md)

| # | Issue | Severity |
|---|-------|----------|
| 1 | OLX blocks datacenter IPs — scraper returns 0 results in Docker | High |
| 2 | `process_urls_list` uses `chord(group(...), callback)` inside task, causing RuntimeError | Medium |
| 3 | 422 on `/products/by-url` for some URLs during `save_product` | Medium |
| 4 | Mercado Livre has low success rate (~19% of scraped URLs) | Low |
| 5 | No frontend UI for manual scraping trigger | Low |

---

## Guardrails (Instructions for AI)

### Git Workflow
- **Never push directly to `main`** — always create a branch for any work.
- **Always work on branches** — no exceptions, even for small fixes.
- **Branch naming convention**: `<type>/<short-description>` (e.g., `fix/olx-scraper-timeout`, `feat/manual-scraping-trigger`).
- **Never rewrite history on shared branches** — no `force-push` unless explicitly approved.

### Commit Messages
- **Language**: English only.
- **Format**: Follow [Conventional Commits](https://www.conventionalcommits.org/):
  ```
  <type>(<scope>): <short description>
  ```
- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.
- **Scope**: The affected component (e.g., `backend`, `scrapers`, `frontend`, `infra`).
- **Body**: Include when the change is non-obvious — explain *why*, not *what*.
- **Examples**:
  ```
  fix(scrapers): add retry logic to OLX scraper
  feat(frontend): add manual scraping trigger button
  chore(infra): add healthcheck to docker-compose services
  ```

### Pull Requests
- **Language**: English only.
- **Title format**: Same as commit messages — `<type>(<scope>): <description>`.
- **Description template**:
  ```markdown
  ## What
  Brief summary of what this PR changes.

  ## Why
  Problem being solved or feature being added.

  ## How
  Key implementation details (if non-trivial).

  ## Checklist
  - [ ] Tests added/updated
  - [ ] Lint and type checks pass
  - [ ] Manual testing done (if applicable)
  ```
- **Always request review** from at least one human before merging.
- **Never auto-merge** — always wait for explicit user approval.

### Code Style
- **Python**: Always use Ruff for lint and format. Strict type hints (MyPy).
- **TypeScript**: Strict mode. ESLint with typescript-eslint.
- **Identifiers**: Always in English.
- **Prefer composition over inheritance**.
- **Keep functions small and single-responsibility**.

### Architecture
- **Never** modify scrapers to access the database directly — communication is exclusively via HTTP with the backend API.
- **Respect** the JSON:API spec on backend endpoints.
- **Maintain** clear separation: entities → use_cases → infrastructure → interfaces.
- **Frontend**: Use services + hooks + context, never direct HTTP calls in components.

### Tests
- **Always** run tests after code changes.
- **Always** run lint/type check before proposing commits.
- **Maintain** minimum 60% coverage (required by CI).
- **Create tests** for new features or bug fixes.
- **Never** delete or disable tests to make CI pass — fix the root cause.

### Docker & Infra
- **Do not** remove healthchecks or security configs from docker-compose.
- **Do not** commit `.env` files with secrets — use `.env.example` as template.
- Tests run **outside** Docker (locally with pytest/vitest).
- **Always** verify that `docker-compose.yml` changes don't break service dependencies.

### Scrapers
- **Always** use `ScraperFactory` to instantiate scrapers.
- **Respect** `RotatingUserAgentMixin` to avoid blocks.
- **Never** hardcode URLs or credentials — use environment variables.
- **Handle** network failures gracefully (retries, timeouts, fallbacks).

### Security & Sensitive Data
- **Always prioritize security** — treat every piece of code as if it could be publicly exposed.
- **Never commit secrets, tokens, API keys, passwords, or credentials** — use `.env` files and environment variables.
- **Always verify `.gitignore`** before staging files to ensure sensitive data is excluded.
- **Use `.env.example`** as a template with placeholder values (never real secrets).
- **Never expose** secrets, tokens, or keys in logs, error messages, stack traces, or code comments.
- **Always** use `bcrypt` for password hashing.
- **Validate** JWT on protected endpoints.
- **Run** Bandit for security analysis on Python code.
- **Never** disable security middleware or validation without explicit approval.
- **Before any push**, double-check for accidentally committed sensitive files (`.env`, `*.pem`, `*.key`, etc.).

### Git Pre-Push Checklist
- [ ] No secrets, tokens, or credentials in the diff
- [ ] `.gitignore` covers all sensitive files (`.env`, `*.key`, `*.pem`, `credentials.json`)
- [ ] No hardcoded URLs with authentication tokens
- [ ] No debug logging that exposes sensitive data
- [ ] Run `git diff --staged` and visually inspect before pushing
- [ ] Confirm branch is not `main` — never push directly to `main`

### AI Behavior
- **Always** read existing files before modifying — never assume content.
- **Confirm** with the user before destructive actions (deleting files, branches, git resets).
- **Document** architectural decisions in `PLAN.md` when relevant.
- **Explain** shell commands before running them if they modify the filesystem or system state.
- **Keep responses concise** — avoid unnecessary commentary unless asked.
- **When in doubt**, ask rather than assume.
