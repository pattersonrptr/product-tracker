from itertools import islice

from src.product_scrapers.scrapers.interfaces.scraper_interface import ScraperInterface


class ScraperManager:
    def __init__(self, scraper: ScraperInterface):
        self.scraper = scraper

    def get_products_urls(self, search):
        print(f"🔎 Searching term: {search} with {self.scraper}")
        return self.scraper.search(search)

    def scrape_product(self, url):
        print(f"🛒 Get products data for {url} with {self.scraper}")
        return self.scraper.scrape_data(url)

    def update_product(self, product: dict):
        print(f"🔄 Updating product for URL: {product['url']}")
        product_data = self.scraper.update_data(product)
        return product_data

    @staticmethod
    def get_urls_to_update(existing_urls, urls):
        new_urls = list(set(urls) - set(existing_urls))

        print(f"➡ New: {len(new_urls)}")
        print(f"➡ Existing: {len(existing_urls)}")
        print(f"➡ Found {len(urls)} URLs, {len(new_urls)} are new")

        return new_urls

    def split_search_urls(self, search_results: dict, chunk_size: int):
        print(
            f"📥 Processing {len(search_results['urls'])} URLs of {search_results['search']}"
        )

        urls = self._get_search_urls(search_results)
        chunks = self._chunk_urls(
            urls=urls,
            chunk_size=chunk_size,
        )
        return chunks

    @staticmethod
    def _get_search_urls(search_results: dict):
        return [url for url in search_results["urls"]]

    @staticmethod
    def _chunk_urls(urls: list, chunk_size: int):
        it = iter(urls)
        return iter(lambda: list(islice(it, chunk_size)), [])
