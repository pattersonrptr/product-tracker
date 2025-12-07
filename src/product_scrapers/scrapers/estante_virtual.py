import datetime
import json

from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from src.product_scrapers.scrapers.base.requests_scraper import RequestScraper
from src.product_scrapers.scrapers.interfaces.scraper_interface import ScraperInterface
from src.product_scrapers.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)


class EstanteVirtualScraper(ScraperInterface, RequestScraper, RotatingUserAgentMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://www.estantevirtual.com.br"

    def headers(self):
        custom_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
        }
        random_user_agent = self.get_random_user_agent()

        if random_user_agent:
            custom_headers["User-Agent"] = random_user_agent
        return custom_headers

    def search(self, search_term: str) -> list[str]:
        page_number = 0
        has_next = True
        all_links = []

        while has_next:
            page_number += 1

            params = {
                "q": quote_plus(search_term),
                "searchField": "titulo-autor",
                "page": f"{page_number}",
            }

            resp = self.retry_request(
                f"{self.BASE_URL}/busca/api",
                self.headers(),
                params=params,
            )

            if page_number == resp.json().get("totalPages"):
                has_next = False

            urls = self._get_products_list(resp.json())
            all_links.extend(urls)

        return all_links

    def _get_products_list(self, data: dict) -> list:
        return [f"{self.BASE_URL}{item['productSlug']}" for item in data["parentSkus"]]

    def scrape_data(self, url: str) -> dict:
        resp = self._fetch_page(url)
        soup = self._parse_html(resp.content)
        data = self._extract_initial_state(soup)

        if not data:
            return {}

        product_info = self._extract_product_info(data)
        price = self._extract_price(product_info)
        description = self._extract_description(product_info)
        seller = self._extract_seller(product_info)
        location = self._extract_location(product_info)
        image_url = self._extract_image(product_info)
        is_available = self._extract_is_available(product_info)
        product_id = product_info.get("id", int(datetime.datetime.now().timestamp()))

        return {
            "url": url,
            "title": f"{product_info.get('name', '')} | {product_info.get('author', '')}",
            "price": f"{price:.2f}" if price else "",
            "description": description,
            "source_product_code": f"EV - {product_id}",
            "city": location,
            "state": "not found",
            "seller_name": seller,
            "is_available": is_available,
            "image_urls": image_url,
            "source_metadata": {},
        }

    def _fetch_page(self, url: str):
        resp = self.retry_request(url)
        resp.raise_for_status()
        return resp

    def _parse_html(self, content: bytes) -> BeautifulSoup:
        return BeautifulSoup(content, "html.parser")

    def _extract_initial_state(self, soup: BeautifulSoup) -> dict:
        script_tag = soup.find(
            "script", string=lambda t: t and "window.__INITIAL_STATE__" in t
        )
        if not script_tag:
            return {}
        json_data = script_tag.string.split("=", 1)[1].strip().rstrip(";")
        return json.loads(json_data)

    def _extract_product_info(self, data: dict) -> dict:
        return data.get("Product", {})

    def _extract_prices(self, product_info: dict) -> list:
        grouper = product_info.get("grouper", {})
        group_products = grouper.get("groupProducts", {})
        prices = []
        for condition in ["novo", "usado"]:
            if condition in group_products:
                price = (
                    group_products[condition].get("salePrice", 0) / 100
                )  # Convert from cents
                prices.append(price)
        return prices

    def _extract_price(self, product_info: dict) -> float:
        sale_in_cents = (
            product_info.get("currentProduct", {}).get("price", {}).get("saleInCents")
        )

        if sale_in_cents is None:
            raise ValueError("Price not found in product info")
        return sale_in_cents / 100

    def _extract_description(self, product_info: dict) -> str:
        return product_info.get("currentProduct", {}).get("description", "")

    def _extract_seller(self, product_info: dict) -> str:
        return (
            product_info.get("currentProduct", {})
            .get("price", {})
            .get("seller")
            .get("name", "Seller not found")
        )

    def _extract_location(self, product_info: dict) -> str:
        grouper = product_info.get("grouper", {})
        group_products = grouper.get("groupProducts", {})
        for condition in ["novo", "usado"]:
            if condition in group_products:
                prices_list = group_products[condition].get("prices", [])
                if prices_list:
                    return prices_list[0].get("city", "")
        return ""

    def _extract_image(self, product_info: dict) -> str:
        # window.__INITIAL_STATE__["Product"]["currentProduct"]["images"]["details"][0]
        img_details = (
            product_info.get("currentProduct", {}).get("images", {}).get("details", [])
        )
        if img_details:
            return f"https://static.estantevirtual.com.br{img_details[0]}"
        return ""

    def _extract_is_available(self, product_info: dict) -> bool:
        return product_info.get("currentProduct", {}).get("available", False)

    def _extract_source_product_code(self, product_info: dict) -> str:
        sku = product_info.get("currentProduct", {}).get("sku", "")
        return f"EV - {sku}"

    def update_data(self, product: dict) -> dict:
        data = self.scrape_data(product["url"])
        return {**product, **data}

    def __str__(self):
        return "Estante Virtual Scraper"
