import logging
import os
from datetime import datetime, timedelta

import requests
from celery import Celery, chord, group

from src.product_scrapers.api.api_client import ApiClient
from src.product_scrapers.scrapers.factory.scraper_factory import ScraperFactory
from src.product_scrapers.scrapers.manager.scraper_manager import ScraperManager

logger = logging.getLogger(__name__)

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
app = Celery(main="product_scrapers", broker=broker_url, backend="redis://redis:6379/0")


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


@app.task(name="src.product_scrapers.celery.tasks.run_scraper_search")
def run_scraper_search(search_config_id: int):
    """Dispatch parallel search tasks for each active source website in a search config."""
    client = ApiClient(get_celery_worker_token())
    search_config = client.get_search_config_by_id(search_config_id)

    if not search_config:
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
        logger.warning(
            "No active source websites for search config %s", search_config_id
        )
        return {"status": "skipped", "message": "No active source websites"}

    return group(
        run_search.s(s["search_term"], s["scraper_name"], s["search_config_id"])
        for s in searches
    )()


@app.task(name="src.product_scrapers.celery.tasks.run_search")
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


@app.task(name="src.product_scrapers.celery.tasks.process_urls_list")
def process_urls_list(
    search_results: dict,
    scraper_name: str,
    search_config_id: int,
    log_id: str | None = None,
):
    """Split URLs into chunks and dispatch scraping tasks for each chunk."""
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    chunks = scraper.split_search_urls(search_results, 100)

    task_group = group(
        chord(
            scrape_product_page.s(url, scraper_name).set(countdown=5) for url in chunk
        )(save_products.s(scraper_name, search_config_id, log_id))
        for chunk in chunks
    )

    return task_group.apply_async()


@app.task(name="src.product_scrapers.celery.tasks.scrape_product_page")
def scrape_product_page(url: str, scraper_name: str):
    """Scrape a single product page and return the extracted data."""
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    try:
        product_data = scraper.scrape_product(url)
        return {"status": "success", "data": product_data}
    except Exception as e:
        return {"status": "error", "url": url, "message": str(e)}


@app.task(name="src.product_scrapers.celery.tasks.save_products")
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
        else:
            created_product = client.create_product(product_data)
            if created_product:
                product_id = created_product.get("id")
                current_price = product_data.get("current_price")
                if product_id and current_price is not None:
                    client.create_price_history(product_id, current_price)
                created += 1

    _finish_log(
        client,
        search_config_id,
        log_id,
        status="success",
        results_count=len(successful),
    )
    return {"status": "success", "created": created, "processed": len(successful)}


@app.task(name="src.product_scrapers.celery.tasks.run_scraper_update")
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


@app.task(name="src.product_scrapers.celery.tasks.update_product")
def update_product(product: dict, scraper_name: str):
    """Re-scrape a single product and return fresh data."""
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    try:
        product_data = scraper.update_product(product)
        return {"status": "success", "data": product_data}
    except Exception as e:
        return {"status": "error", "url": product.get("url"), "message": str(e)}


@app.task(name="src.product_scrapers.celery.tasks.update_products")
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
    """Update or create a SearchExecutionLog entry to mark a search as finished."""
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


app.conf.timezone = "America/Sao_Paulo"
app.conf.beat_scheduler = "src.product_scrapers.celery.beat_schedule.DynamicDBScheduler"
