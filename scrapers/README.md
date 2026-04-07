# 🕷️ Product Tracker — Scrapers

Celery workers and web scraping engines for the Product Tracker system.

This service is **fully decoupled** from the backend — it communicates
exclusively via HTTP through the backend's REST API.

---

## Tech Stack

| Component | Technology |
|---|---|
| Task queue | Celery 5 |
| Broker | Redis |
| HTTP scraping | Requests + Cloudscraper + BeautifulSoup4 |
| Monitoring | Flower |
| Language | Python 3.11+ |

---

## Supported Platforms

| Platform | Scraper |
|---|---|
| OLX | `olx.py` |
| Mercado Livre | `mercado_livre.py` |
| Enjoei | `enjoei.py` |
| Estante Virtual | `estante_virtual.py` |

---

## Architecture

```
scrapers/
└── src/
    ├── api/              ← HTTP client for backend communication
    │   └── api_client.py
    ├── celery/           ← Task definitions and scheduling
    │   ├── tasks.py
    │   └── beat_schedule.py
    ├── scrapers/         ← Scraping engines
    │   ├── interfaces/   ← ScraperInterface (ABC)
    │   ├── base/         ← RequestScraper (shared HTTP logic)
    │   ├── factory/      ← ScraperFactory
    │   ├── manager/      ← ScraperManager (orchestration)
    │   ├── mixins/       ← RotatingUserAgentMixin
    │   ├── resources/    ← user-agents.json
    │   ├── olx.py
    │   ├── enjoei.py
    │   ├── mercado_livre.py
    │   └── estante_virtual.py
    └── tests/
```

---

## Running Locally

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest src/tests/ -v

# Start a worker (requires Redis + backend running)
celery -A src.celery.tasks worker --loglevel=info

# Start beat scheduler
celery -A src.celery.tasks beat --loglevel=info

# Start Flower monitoring
celery -A src.celery.tasks flower --port=5555
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `API_URL` | Backend API base URL | `http://web:8000` |
| `CELERY_BROKER_URL` | Redis broker URL | `redis://redis:6379/0` |
| `CELERY_WORKER_USERNAME` | Auth username for API access | — |
| `CELERY_WORKER_PASSWORD` | Auth password for API access | — |

---

## Adding a New Scraper

1. Create `src/scrapers/new_site.py` implementing `ScraperInterface`
2. Register it in `src/scrapers/factory/scraper_factory.py`
3. Add the source website via the backend API
4. No changes needed in `backend/` or `frontend/`
