import datetime

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from src.product_scrapers.scrapers.base.requests_scraper import RequestScraper
from src.product_scrapers.scrapers.interfaces.scraper_interface import ScraperInterface
from src.product_scrapers.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)


class MercadoLivreScraper(ScraperInterface, RequestScraper, RotatingUserAgentMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://lista.mercadolivre.com.br"

    def headers(self):
        custom_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
        }
        random_user_agent = self.get_random_user_agent()

        if random_user_agent:
            custom_headers["User-Agent"] = random_user_agent
        return custom_headers

    def _extract_links(self, html: str) -> list:
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a in soup.select(".poly-component__title-wrapper a"):
            href = a.get("href", "")
            if not href.startswith("https://click1"):
                links.append(href)

        return links

    def _get_next_url(self, total_links: int, search_term: str) -> str:
        if not total_links:
            return ""
        start_from = total_links + 1

        return f"{self.BASE_URL}/{search_term}_Desde_{start_from}_NoIndex_True"

    def search(self, search_term: str) -> list:
        page_number = 1
        total_links = 0
        has_next = True
        all_links = []
        search_url = f"{self.BASE_URL}/{search_term}"

        while has_next:
            try:
                resp = self.retry_request(search_url, self.headers())
                html_content = resp.text if resp.text else ""

                if not html_content:
                    break

                links = self._extract_links(html_content)

                if not links:
                    break

                all_links.extend(links)
                print(f"Page Number {page_number}")
                page_number += 1
                total_links = total_links + len(links)
                search_url = self._get_next_url(total_links, search_term)
                has_next = search_term != ""

            except Exception as e:
                print(f"Error on page {page_number}: {str(e)}")
                print(f"Search URL: {search_url}")
                break

        return all_links

    def scrape_data(self, url: str) -> dict:
        resp = self.retry_request(url, self.headers())
        html_content = resp.content
        soup = BeautifulSoup(html_content, "html.parser")
        title = self._extract_title(soup)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        source_product_code = f"ML - {int(datetime.datetime.now().timestamp())}"
        is_available = self._extract_availability(soup)
        image_url = self._extract_image_src(soup)

        return {
            "url": url,
            "title": title,
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

    def _extract_price(self, soup):
        price_element = soup.find("meta", itemprop="price")
        if price_element:
            return price_element.get("content", "")
        return ""

    def _extract_title(self, soup):
        title_element = soup.find("h1", class_="ui-pdp-title")
        title = title_element.get_text(strip=True) if title_element else ""
        return title

    def _extract_description(self, soup):
        description_element = soup.find("p", {"class": "ui-pdp-description__content"})
        description = (
            description_element.get_text(strip=True) if description_element else ""
        )
        return description

    def _extract_availability(self, soup) -> bool:
        try:
            stock_info = soup.select_one(".ui-pdp-stock-information__title")
            if stock_info and "disponível" in stock_info.get_text(strip=True).lower():
                return True
        except Exception:
            pass
        return False

    def _extract_product_code(self, url):
        fragment = urlparse(url).fragment
        params = parse_qs(fragment)
        return params.get("wid", [None])[0]

    def _extract_image_src(self, soup):
        try:
            img = soup.select_one("img.ui-pdp-image.ui-pdp-gallery__figure__image")
            return img["src"] if img and img.has_attr("src") else None
        except Exception:
            return None

    def update_data(self, product: dict) -> dict:
        data = self.scrape_data(product["url"])
        return {**product, **data}

    def __str__(self):
        return "Mercado Livre Scraper"
