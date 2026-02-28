import logging
from itertools import islice

from src.product_scrapers.scrapers.interfaces.scraper_interface import ScraperInterface

logger = logging.getLogger(__name__)


class ScraperManager:
    def __init__(self, scraper: ScraperInterface):
        self.scraper = scraper

    def get_products_urls(self, search):
        logger.info("🔎 Searching term: %s with %s", search, self.scraper)
        return self.scraper.search(search)

    def scrape_product(self, url):
        logger.info("🛒 Get products data for %s with %s", url, self.scraper)
        return self.scraper.scrape_data(url)

    def update_product(self, product: dict):
        logger.info("🔄 Updating product for URL: %s", product["url"])
        product_data = self.scraper.update_data(product)
        return product_data

    @staticmethod
    def get_urls_to_update(existing_urls, urls):
        new_urls = list(set(urls) - set(existing_urls))

        logger.info("➡ New: %d", len(new_urls))
        logger.info("➡ Existing: %d", len(existing_urls))
        logger.info("➡ Found %d URLs, %d are new", len(urls), len(new_urls))

        return new_urls

    def split_search_urls(self, search_results: dict, chunk_size: int):
        logger.info(
            "📥 Processing %d URLs of %s",
            len(search_results["urls"]),
            search_results["search"],
        )

        urls = self._get_search_urls(search_results)
        chunks = self._chunk_urls(
            urls=urls,
            chunk_size=chunk_size,
        )
        return chunks

    @staticmethod
    def _get_search_urls(search_results: dict):
        return list(search_results["urls"])

    @staticmethod
    def _chunk_urls(urls: list, chunk_size: int):
        it = iter(urls)
        return iter(lambda: list(islice(it, chunk_size)), [])
