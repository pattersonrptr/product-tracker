import asyncio
import json
import logging
from urllib.parse import urlencode

from src.scrapers.base.playwright_scraper import PlaywrightScraper
from src.scrapers.interfaces.scraper_interface import ScraperInterface
from src.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)

logger = logging.getLogger(__name__)


class EnjoeiScraper(ScraperInterface, PlaywrightScraper, RotatingUserAgentMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://enjusearch.enjoei.com.br"

    @staticmethod
    def _build_default_headers():
        return {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
        }

    def headers(self) -> dict:
        custom_headers = self._build_default_headers()
        random_user_agent = self.get_random_user_agent()
        if random_user_agent:
            custom_headers["User-Agent"] = random_user_agent
        return custom_headers

    async def _get_search_data_async(
        self, term: str, after: str | None = None
    ) -> dict:
        """Fetch search data via Playwright by loading the GraphQL JSON endpoint."""
        params = {
            "first": "50",
            "query_id": "7d3ea67171219db36dfcf404acab5807",
            "search_id": "88d3a54e-085a-46bc-a1f8-9726ee34424a-1743974498480",
            "term": term,
        }

        if after:
            params["after"] = after

        url = f"{self.BASE_URL}/graphql-search-x?{urlencode(params)}"

        context = None
        try:
            context, page = await self.fetch_page(url, wait_until="networkidle")
            body_text = await page.locator("body").text_content()
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                logger.warning("Enjoei: non-JSON response: %s", body_text[:200])
                return {}
        except Exception as e:
            logger.error("Enjoei: failed to fetch search data: %s", e)
            return {}
        finally:
            if context:
                await context.close()

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
        """Synchronous entry point — runs the async search loop."""
        return self._run_async(self._search_async(search_term))

    async def _search_async(self, search_term: str) -> list[str]:
        all_urls: list[str] = []
        cursor = None
        max_iterations = 20

        for _ in range(max_iterations):
            response_data = await self._get_search_data_async(
                term=search_term, after=cursor
            )
            if not response_data:
                logger.warning("Enjoei: no response data, stopping")
                break

            urls, cursor = self._extract_links(response_data)
            all_urls.extend(urls)
            logger.debug("Enjoei: %d URLs collected so far", len(all_urls))

            if not cursor:
                break

            await asyncio.sleep(1.5)

        if not all_urls:
            raise Exception("No results found")

        return all_urls

    def scrape_data(self, url: str) -> dict:
        """Synchronous entry point — runs the async scrape."""
        return self._run_async(self._scrape_data_async(url))

    async def _scrape_data_async(self, url: str) -> dict:
        context = None
        try:
            context, page = await self.fetch_page(url, wait_until="networkidle")
            body_text = await page.locator("body").text_content()
            try:
                data = json.loads(body_text)
            except json.JSONDecodeError:
                logger.error("Enjoei: failed to parse product data from %s", url)
                raise Exception("Invalid product data") from None
        except Exception as e:
            logger.error("Enjoei: failed to scrape data from %s: %s", url, e)
            raise
        finally:
            if context:
                await context.close()

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
