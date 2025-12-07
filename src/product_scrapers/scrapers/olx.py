import html
import json

from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from typing import Dict, List, Any

from src.product_scrapers.scrapers.base.requests_scraper import RequestScraper
from src.product_scrapers.scrapers.interfaces.scraper_interface import ScraperInterface
from src.product_scrapers.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)


class OLXScraper(ScraperInterface, RequestScraper, RotatingUserAgentMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://www.olx.com.br/brasil"

    def headers(self):
        custom_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
            # ...
        }
        random_user_agent = self.get_random_user_agent()

        if random_user_agent:
            custom_headers["User-Agent"] = random_user_agent
        return custom_headers

    def search(self, search_term: str) -> List[str]:
        page_number = 1
        results = []

        while True:
            search_url = self._build_search_url(search_term, page_number)
            resp = self.retry_request(search_url, self.headers())
            html_content = resp.text if resp.text else ""

            if not html_content:
                break

            try:
                links = self._extract_links(html_content)

                if not links:
                    break
            except Exception as e:
                print(f"Error extracting links: {e}")
                break

            results.extend(links)
            page_number += 1

        if not results:
            raise Exception("No results found")

        return results

    def scrape_data(self, url: str) -> Dict[str, Any]:
        resp = self.retry_request(url, self.headers())
        html_content = resp.content
        soup = BeautifulSoup(html_content, "html.parser")
        json_data = self._extract_json_data(soup)

        title = json_data.get("subject")
        description = json_data.get("body")
        source_product_code = f"OLX - {json_data.get('listId')}"
        price = (
            json_data.get("priceValue", "")
            .replace("R$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        images = json_data.get("images", [])
        image_url = images[0].get("original", "") if images else ""
        seller_name = json_data.get("user", {}).get("name")
        city = json_data.get("location", {}).get("municipality")
        state = json_data.get("location", {}).get("uf")

        return {
            "url": url,
            "title": title,
            "price": price,
            "description": description,
            "source_product_code": source_product_code,
            "city": city,
            "state": state,
            "seller_name": seller_name,
            "is_available": True if price else False,
            "image_urls": image_url,
            "source_metadata": {},
        }

    def update_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        data = self.scrape_data(product["url"])
        if "id" in product:
            data["id"] = product["id"]
        return data

    def _build_search_url(self, search_term: str, page_number: int = 1) -> str:
        encoded_search = quote_plus(search_term.encode("utf-8"))
        return f"{self.BASE_URL}?q={encoded_search}&o={page_number}"

    def _extract_links(self, html_content: str) -> List[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        urls = []

        # json_str = document.getElementById("__NEXT_DATA__").innerHTML
        data_element = soup.find("script", {"id": "__NEXT_DATA__"})

        if not data_element:
            raise Exception("No data found")

        data = json.loads(data_element.string)
        ads_data = data.get("props", {}).get("pageProps", {}).get("ads")

        if not ads_data:
            raise Exception("No ads data found")

        for ad in ads_data:
            url = ad.get("url")

            if url and url not in urls:
                urls.append(url)

        return urls

    def _extract_json_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        script = soup.find("script", {"id": "initial-data"})
        if not script:
            return {}
        decoded_data = html.unescape(script["data-json"])
        return json.loads(decoded_data).get("ad", {})

    def __str__(self):
        return "OLX Scraper"
