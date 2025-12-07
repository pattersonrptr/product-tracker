from requests import Response

from src.product_scrapers.scrapers.base.requests_scraper import RequestScraper
from src.product_scrapers.scrapers.interfaces.scraper_interface import ScraperInterface
from src.product_scrapers.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)


class EnjoeiScraper(ScraperInterface, RequestScraper, RotatingUserAgentMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://enjusearch.enjoei.com.br"

    def headers(self):
        custom_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
        }
        random_user_agent = self.get_random_user_agent()

        if random_user_agent:
            custom_headers["User-Agent"] = random_user_agent
        return custom_headers

    def _get_search_data(self, term: str, after: str = None) -> Response:
        params = {
            "first": "50",
            "query_id": "7d3ea67171219db36dfcf404acab5807",
            "search_id": "88d3a54e-085a-46bc-a1f8-9726ee34424a-1743974498480",
            "term": term,
        }

        if after:
            params["after"] = after

        return self.retry_request(
            f"{self.BASE_URL}/graphql-search-x",
            self.headers(),
            params=params,
        )

    def _extract_links(self, data: dict) -> tuple:
        urls = []
        cursor = None
        result_pages_url = "https://pages.enjoei.com.br/products"

        try:
            edges = (
                data.get("data", {})
                .get("search", {})
                .get("products", {})
                .get("edges", [])
            )
            for edge in edges:
                node = edge["node"]
                if "id" in node:
                    product_id = node["id"]
                    urls.append(f"{result_pages_url}/{product_id}/v2.json")

                    if "cursor" in edge:
                        cursor = edge["cursor"]

        except (KeyError, TypeError, AttributeError):
            pass

        return urls, cursor

    def search(self, search_term: str) -> list[str]:
        all_urls = []
        cursor = None
        while True:
            response = self._get_search_data(term=search_term, after=cursor)
            urls, cursor = self._extract_links(response.json())
            all_urls.extend(urls)
            if not cursor:
                break
        return all_urls

    def scrape_data(self, url: str) -> dict:
        response = self.retry_request(url, self.headers())
        data = response.json()
        url = data["canonical_url"]
        price_dict = data.get("fallback_pricing", {}).get("price", {})
        price = price_dict.get("listed") or price_dict.get("sale") or "0"
        description = data.get("description", "")
        photo_codes = data.get("photos")
        photo_code = photo_codes[0] if photo_codes else ""
        image_url = (
            f"https://photos.enjoei.com.br/{url.split('/')[-1]}/1200xN/{photo_code}"
            if photo_code
            else ""
        )
        is_available = data.get("fallback_pricing", {}).get("state", "") == "published"
        source_product_code = f"EJ - {data.get('id')} "

        return {
            "url": url,
            "title": data.get("title"),
            "price": price,
            "description": description,
            "source_product_code": source_product_code,
            "city": "not found",
            "state": "not found",
            "seller_name": "not found",
            "is_available": is_available,
            "image_urls": image_url,
            "source_metadata": {},
        }

    def update_data(self, product: dict) -> dict:
        product_code = product["url"].split("-")[-1]
        api_url = f"https://pages.enjoei.com.br/products/{product_code}/v2.json"
        updated_data = self.scrape_data(api_url)
        return {**product, **updated_data}

    def __str__(self):
        return "Enjoei Scraper"
