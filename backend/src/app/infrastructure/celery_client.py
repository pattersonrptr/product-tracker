"""Minimal Celery client for dispatching tasks from the backend API.

The backend doesn't run Celery workers — it only uses `send_task` to
push messages onto the Redis broker so the scraper workers pick them up.
"""

import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(main="scrapers", broker=broker_url, backend=broker_url)


def dispatch_scraper_search(search_config_id: int) -> str:
    """Send ``run_scraper_search`` to the Celery broker.

    Returns the Celery task id so callers can track execution if needed.
    """
    result = celery_app.send_task(
        "src.celery.tasks.run_scraper_search",
        args=[search_config_id],
    )
    return result.id
