import os
import requests

from datetime import datetime, timedelta
from celery import Celery, group, chord

from src.product_scrapers.api.api_client import ApiClient
from src.product_scrapers.scrapers.factory.scraper_factory import ScraperFactory
from src.product_scrapers.scrapers.manager.scraper_manager import ScraperManager

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
app = Celery(main="product_scrapers", broker=broker_url, backend="redis://redis:6379/0")


def get_celery_worker_token():
    api_base_url = os.getenv("API_URL", "web:8000")
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
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"🔴 Error when trying to retrieve Celery worker token: {e}")
        return None


@app.task(name="src.product_scrapers.celery.tasks.run_scraper_search")
def run_scraper_search(search_config_id: int):
    search_config = ApiClient(get_celery_worker_token()).get_search_configs_by_id(
        search_config_id
    )

    searches = []
    for source_website in search_config.get("source_websites", []):
        if source_website.get("is_active"):
            searches.append(
                {
                    "search_term": search_config["search_term"],
                    "scraper_name": source_website["name"],
                }
            )

    return group(
        run_search.s(search["search_term"], search["scraper_name"])
        for search in searches
    )()


@app.task(name="src.product_scrapers.celery.tasks.run_search")
def run_search(search: str, scraper_name: str):
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    existing_urls = ApiClient(get_celery_worker_token()).get_existing_product_urls(
        scraper_name
    )
    urls = list(scraper.get_products_urls(search))
    new_urls = scraper.get_urls_to_update(existing_urls, urls)

    process_urls_list.apply_async(
        args=[
            {"status": "success", "search": search, "urls": new_urls},
            scraper_name,
        ],
        countdown=10,
    )
    return {"status": "success", "search": search, "urls": new_urls}


@app.task(name="src.product_scrapers.celery.tasks.process_urls_list")
def process_urls_list(search_results: dict, scraper_name: str):
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))
    chunks = scraper.split_search_urls(search_results, 100)

    task_group = group(
        chord(
            scrape_product_page.s(url, scraper_name).set(countdown=5) for url in chunk
        )(save_products.s(scraper_name))
        for chunk in chunks
    )

    return task_group.apply_async()


@app.task(name="src.product_scrapers.celery.tasks.scrape_product_page")
def scrape_product_page(url: str, scraper_name: str):
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))

    try:
        product_data = scraper.scrape_product(url)
        return {"status": "success", "data": product_data}
    except Exception as e:
        return {"status": "error", "url": url, "message": str(e)}


@app.task(name="src.product_scrapers.celery.tasks.save_products")
def save_products(results, scraper_name: str):
    if results:
        source_website = ApiClient(
            get_celery_worker_token()
        ).get_source_website_by_name(scraper_name.lower())
        website_id = source_website.get("id")
        successful = [
            {**r["data"], **{"source_website_id": website_id}}
            for r in results
            if r["status"] == "success"
        ]

        if successful:
            created = ApiClient(get_celery_worker_token()).create_new_products(
                successful
            )
            return {"status": "success", "created": created}

    return {"status": "error", "message": "No products to save"}


@app.task(name="src.product_scrapers.celery.tasks.run_scraper_update")
def run_scraper_update(scraper_name: str):
    cutoff_date = (datetime.today() - timedelta(days=30)).date()
    products = ApiClient(get_celery_worker_token()).get_products(
        {"updated_before": cutoff_date}
    )

    return chord(
        update_product.s(product, scraper_name).set(countdown=10)
        for product in products
    )(update_products.s(scraper_name))


@app.task(name="src.product_scrapers.celery.tasks.update_product")
def update_product(product: dict, scraper_name: str):
    scraper = ScraperManager(ScraperFactory().create_scraper(scraper_name))

    try:
        product_data = scraper.update_product(product)
        return {"status": "success", "data": product_data}
    except Exception as e:
        return {"status": "error", "url": product["url"], "message": str(e)}


@app.task(name="src.product_scrapers.celery.tasks.update_products")
def update_products(results, scraper_name: str):
    if results:
        source_website = ApiClient(
            get_celery_worker_token()
        ).get_source_website_by_name(scraper_name.lower())
        website_id = source_website.get("id")
        successful = [
            {**r["data"], **{"source_website_id": website_id}}
            for r in results
            if r["status"] == "success"
        ]

        if successful:
            updated = ApiClient(get_celery_worker_token()).update_product_list(
                successful
            )
            return {"status": "success", "updated": updated}

    return {"status": "error", "message": "No products to update"}


app.conf.timezone = "America/Sao_Paulo"
app.conf.beat_scheduler = "src.product_scrapers.celery.beat_schedule.DynamicDBScheduler"
