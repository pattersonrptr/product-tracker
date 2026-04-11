import logging
import os
import random
from datetime import datetime, timedelta

import redis
import requests

from celery import Celery, chord, group
from src.api.api_client import ApiClient
from src.scrapers.factory.scraper_factory import ScraperFactory
from src.scrapers.manager.scraper_manager import ScraperManager

logger = logging.getLogger(__name__)

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
app = Celery(main="scrapers", broker=broker_url, backend="redis://redis:6379/0")

_redis = redis.Redis.from_url(broker_url, decode_responses=True)


def get_celery_worker_token():
    api_base_url = os.getenv("API_URL", "http://web:8000")
    auth_url = f"{api_base_url}/auth/login"
    payload = {
        "username": os.getenv("CELERY_WORKER_USERNAME"),
        "password": os.getenv("CELERY_WORKER_PASSWORD"),
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": "",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(auth_url, data=payload, headers=headers)
        response.raise_for_status()
        # Response is JSON:API: {"data": {"attributes": {"access_token": "..."}}}
        body = response.json()
        token = (
            body.get("data", {}).get("attributes", {}).get("access_token")
            or body.get("access_token")  # fallback for plain JSON
        )
        return token
    except requests.exceptions.RequestException as e:
        logger.error("Error when trying to retrieve Celery worker token: %s", e)
        return None


@app.task(name="src.celery.tasks.run_scraper_search")
def run_scraper_search(search_config_id: int):
    """Dispatch parallel search tasks for each active source website in a search config.

    Uses a Redis lock to prevent the same search config from running
    concurrently.  The lock auto-expires after 30 minutes as a safety net.
    """
    lock_key = f"search_config_lock:{search_config_id}"

    # Try to acquire lock (SET NX with 30-minute TTL)
    if not _redis.set(lock_key, "running", nx=True, ex=1800):
        logger.info(
            "Search config %s is already running (lock held), skipping.",
            search_config_id,
        )
        return {
            "status": "skipped",
            "message": f"Search config {search_config_id} is already running",
        }

    try:
        return _run_scraper_search_locked(search_config_id)
    except Exception:
        # Release lock on unexpected failure so the config can be re-triggered
        _redis.delete(lock_key)
        raise


def _run_scraper_search_locked(search_config_id: int):
    """Inner implementation — called while the Redis lock is held."""
    client = ApiClient(get_celery_worker_token())
    search_config = client.get_search_config_by_id(search_config_id)

    if not search_config:
        _redis.delete(f"search_config_lock:{search_config_id}")
        logger.error("Search config %s not found, skipping.", search_config_id)
        return {
            "status": "error",
            "message": f"Search config {search_config_id} not found",
        }

    searches = []
    for source_website_id in search_config.get("source_website_ids", []):
        # Each id in source_website_ids is an int; we need the name for the scraper factory
        # We fetch the source website to check is_active and retrieve name
        response = requests.get(
            f"{client.base_url}/source-websites/{source_website_id}",
            headers=client.headers,
            timeout=10,
        )
        if response.status_code == 200:
            sw = ApiClient._extract_attributes(response.json())
            if sw.get("is_active"):
                searches.append(
                    {
                        "search_config_id": search_config_id,
                        "search_term": search_config["search_term"],
                        "scraper_name": sw["name"],
                    }
                )

    if not searches:
        _redis.delete(f"search_config_lock:{search_config_id}")
        logger.warning(
            "No active source websites for search config %s", search_config_id
        )
        return {"status": "skipped", "message": "No active source websites"}

    return group(
        run_search.s(s["search_term"], s["scraper_name"], s["search_config_id"])
        for s in searches
    )()


@app.task(name="src.celery.tasks.run_search")
def run_search(search: str, scraper_name: str, search_config_id: int):
    """Run a search for a given term on a given scraper and dispatch URL processing."""
    client = ApiClient(get_celery_worker_token())
    log = client.create_search_execution_log(
        search_config_id=search_config_id,
        status="running",
    )
    log_id = log.get("id")

    try:
        scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
        existing_urls = client.get_existing_product_urls(scraper_name)
        urls = list(scraper.get_products_urls(search))
        new_urls = scraper.get_urls_to_update(existing_urls, urls)

        process_urls_list.apply_async(
            args=[
                {"status": "success", "search": search, "urls": new_urls},
                scraper_name,
                search_config_id,
                log_id,
            ],
            countdown=10,
        )
        return {"status": "success", "search": search, "new_urls_count": len(new_urls)}

    except Exception as e:
        logger.error(
            "Error in run_search for '%s' on '%s': %s", search, scraper_name, e
        )
        client.create_search_execution_log(
            search_config_id=search_config_id,
            status="failed",
            results_count=0,
            error_message=str(e),
        )
        return {"status": "error", "search": search, "message": str(e)}


@app.task(name="src.celery.tasks.process_urls_list")
def process_urls_list(
    search_results: dict,
    scraper_name: str,
    search_config_id: int,
    log_id: str | None = None,
):
    """Split URLs into small batches and dispatch one task per batch.

    Each ``scrape_batch`` task reuses a single browser instance for all
    URLs in its batch, then persists the results — avoiding the memory
    explosion of launching one Chromium process per URL.
    """
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    # Use smaller chunks (20) so each batch finishes in reasonable time
    chunks = list(scraper.split_search_urls(search_results, 20))

    for chunk in chunks:
        scrape_batch.apply_async(
            args=[chunk, scraper_name, search_config_id, log_id],
            countdown=5,
        )

    return {"status": "dispatched", "batches": len(chunks)}


@app.task(name="src.celery.tasks.scrape_batch")
def scrape_batch(
    urls: list[str],
    scraper_name: str,
    search_config_id: int | None = None,
    log_id: str | None = None,
):
    """Scrape a batch of URLs using a single browser, then save results.

    This avoids the memory cost of launching a separate Chromium process
    for every single URL (the old ``scrape_product_page`` approach).

    Rate-limiting is handled by each scraper internally (e.g.
    ``MercadoLivreScraper`` applies its own delays between requests).
    """
    scraper_instance = ScraperFactory().create_scraper(scraper_name)
    scraper = ScraperManager(scraper_instance)
    results = []

    # Shuffle URLs if the scraper requests it (anti-sequential pattern
    # to avoid behavioural detection — e.g. MercadoLivreScraper).
    if getattr(scraper_instance, "_SHUFFLE_URLS", False):
        urls = list(urls)  # copy so we don't mutate the original
        random.shuffle(urls)
        logger.info("🔀 URLs shuffled for %s (%d URLs)", scraper_name, len(urls))

    try:
        for url in urls:
            try:
                product_data = scraper.scrape_product(url)
                results.append({"status": "success", "data": product_data})
            except Exception as e:
                logger.warning("Failed to scrape %s: %s", url, e)
                results.append({"status": "error", "url": url, "message": str(e)})
    finally:
        # Ensure browser is closed and loop is torn down after the batch
        if hasattr(scraper_instance, "stop_sync"):
            scraper_instance.stop_sync()

    # Persist immediately (no chord needed)
    return save_products(results, scraper_name, search_config_id, log_id)


@app.task(name="src.celery.tasks.scrape_product_page")
def scrape_product_page(url: str, scraper_name: str):
    """Scrape a single product page and return the extracted data.

    Kept for backward-compatibility / one-off scrapes.  For bulk work
    prefer ``scrape_batch`` which reuses the browser across URLs.
    """
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    try:
        product_data = scraper.scrape_product(url)
        return {"status": "success", "data": product_data}
    except Exception as e:
        return {"status": "error", "url": url, "message": str(e)}


@app.task(name="src.celery.tasks.save_products")
def save_products(
    results: list,
    scraper_name: str,
    search_config_id: int | None = None,
    log_id: str | None = None,
):
    """Persist scraped products and record price history entries. Finalises the execution log."""
    client = ApiClient(get_celery_worker_token())

    if not results:
        _finish_log(client, search_config_id, log_id, status="success", results_count=0)
        return {"status": "error", "message": "No products to save"}

    source_website = client.get_source_website_by_name(scraper_name.lower())
    website_id = source_website.get("id")

    successful = [
        {**r["data"], "source_website_id": website_id}
        for r in results
        if r.get("status") == "success"
    ]

    if not successful:
        _finish_log(client, search_config_id, log_id, status="success", results_count=0)
        return {"status": "error", "message": "All scraping attempts failed"}

    created = 0
    for product_data in successful:
        url = product_data.get("url")
        if not url:
            continue
        existing = client.get_product_by_url(url)
        if existing:
            product_id = existing.get("id")
            current_price = product_data.get("current_price")
            if product_id and current_price is not None:
                client.create_price_history(product_id, current_price)
            client.update_product(product_id, product_data)
            # Evaluate alerts for the updated product
            if product_id:
                try:
                    client.evaluate_product_alerts(product_id)
                except Exception as e:
                    logger.warning(
                        "Alert evaluation failed for product %s: %s", product_id, e
                    )
        else:
            created_product = client.create_product(product_data)
            if created_product:
                product_id = created_product.get("id")
                current_price = product_data.get("current_price")
                if product_id and current_price is not None:
                    client.create_price_history(product_id, current_price)
                    # Evaluate alerts for the newly created product
                    try:
                        client.evaluate_product_alerts(product_id)
                    except Exception as e:
                        logger.warning(
                            "Alert evaluation failed for product %s: %s",
                            product_id,
                            e,
                        )
                created += 1

    _finish_log(
        client,
        search_config_id,
        log_id,
        status="success",
        results_count=len(successful),
    )

    return {"status": "success", "created": created, "processed": len(successful)}


@app.task(name="src.celery.tasks.run_scraper_update")
def run_scraper_update(scraper_name: str):
    """Re-scrape all products updated more than 30 days ago for a given scraper."""
    cutoff_date = (datetime.today() - timedelta(days=30)).date()
    products = ApiClient(get_celery_worker_token()).get_products(
        {"updated_before": str(cutoff_date), "source_website_name": scraper_name}
    )

    if not products:
        return {"status": "skipped", "message": "No products to update"}

    return chord(
        update_product.s(product, scraper_name).set(countdown=10)
        for product in products
    )(update_products.s(scraper_name))


@app.task(name="src.celery.tasks.update_product")
def update_product(product: dict, scraper_name: str):
    """Re-scrape a single product and return fresh data."""
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    try:
        product_data = scraper.update_product(product)
        return {"status": "success", "data": product_data}
    except Exception as e:
        return {"status": "error", "url": product.get("url"), "message": str(e)}


@app.task(name="src.celery.tasks.update_products")
def update_products(results: list, scraper_name: str):
    """Persist updated product data and record price history entries."""
    client = ApiClient(get_celery_worker_token())

    if not results:
        return {"status": "error", "message": "No products to update"}

    source_website = client.get_source_website_by_name(scraper_name.lower())
    website_id = source_website.get("id")

    successful = [
        {**r["data"], "source_website_id": website_id}
        for r in results
        if r.get("status") == "success"
    ]

    if not successful:
        return {"status": "error", "message": "All update attempts failed"}

    updated = 0
    for product_data in successful:
        product_id = product_data.get("id")
        if not product_id:
            continue
        result = client.update_product(product_id, product_data)
        if result:
            current_price = product_data.get("current_price")
            if current_price is not None:
                client.create_price_history(product_id, current_price)
            updated += 1

    return {"status": "success", "updated": updated}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finish_log(
    client: ApiClient,
    search_config_id: int | None,
    log_id: str | None,
    status: str,
    results_count: int,
    error_message: str | None = None,
):
    """Update or create a SearchExecutionLog entry to mark a search as finished.

    Also releases the Redis lock so the search config can be triggered again.
    """
    if search_config_id is None:
        return
    # The API currently only supports creating logs; if a PATCH endpoint is
    # added later this helper can be updated to use it instead.
    client.create_search_execution_log(
        search_config_id=search_config_id,
        status=status,
        results_count=results_count,
        error_message=error_message,
    )
    # Release lock so the config can be re-triggered
    _redis.delete(f"search_config_lock:{search_config_id}")


app.conf.timezone = "America/Sao_Paulo"
app.conf.beat_scheduler = "src.celery.beat_schedule.DynamicScheduler"


# ---------------------------------------------------------------------------
# Notification tasks
# ---------------------------------------------------------------------------


@app.task(name="src.celery.tasks.send_price_alert_notifications")
def send_price_alert_notifications(search_config_id: int | None = None):
    """Check active price alerts and send email notifications for matching products.

    If search_config_id is provided, only check alerts linked to that config.
    Otherwise, check all active alerts.

    Called automatically after save_products or can be triggered manually.
    """
    client = ApiClient(get_celery_worker_token())
    alerts = client.get_active_price_alerts()

    if search_config_id is not None:
        alerts = [a for a in alerts if a.get("search_config_id") == search_config_id]

    if not alerts:
        logger.info("No active price alerts to notify for config=%s", search_config_id)
        return {"status": "skipped", "message": "No active alerts"}

    results = []
    for alert in alerts:
        alert_id = alert.get("id")
        if not alert_id:
            continue
        try:
            result = client.trigger_price_alert_notification(alert_id)
            results.append({"alert_id": alert_id, "result": result})
        except Exception as e:
            logger.error("Notification failed for alert %s: %s", alert_id, e)
            results.append({"alert_id": alert_id, "error": str(e)})

    sent = sum(
        1
        for r in results
        if r.get("result", {}).get("data", {}).get("attributes", {}).get("status")
        == "sent"
    )
    return {
        "status": "success",
        "alerts_checked": len(alerts),
        "notifications_sent": sent,
    }
