import asyncio
import logging
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

from src.scrapers.base.playwright_scraper import PlaywrightScraper
from src.scrapers.interfaces.scraper_interface import ScraperInterface
from src.scrapers.mixins.rotating_user_agent_mixin import (
    RotatingUserAgentMixin,
)

logger = logging.getLogger(__name__)


class _ProxyBlockedError(Exception):
    """Raised when ML blocks the current proxy (302 → account-verification)."""

    def __init__(self, proxy: dict | None = None, url: str = "") -> None:
        self.proxy = proxy
        super().__init__(f"Proxy blocked by ML: {url}")


class MercadoLivreScraper(ScraperInterface, PlaywrightScraper, RotatingUserAgentMixin):
    """Mercado Livre scraper using Playwright for JS-rendered pages.

    Uses **proxy rotation** to bypass ML's server-side IP reputation
    system.  If ``PROXY_ENABLED=true`` with ``PROXY_*`` env vars, a
    paid proxy is used.  Otherwise, free SOCKS5 proxies are fetched
    and rotated automatically — on block, the next proxy is tried.
    """

    # ML blocks our IP at the server level (302 → account-verification).
    # Proxy rotation gives us clean IPs that ML won't flag.
    _USE_PROXY = True

    # Maximum number of proxy rotation attempts per operation.
    _MAX_PROXY_RETRIES = 5

    # ML blocks old/non-Chrome user-agents, so we always use a modern
    # Chrome UA string instead of the random pool from the mixin.
    _CHROME_UA = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://lista.mercadolivre.com.br"

    @staticmethod
    def _build_default_headers():
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Sec-GPC": "1",
        }

    def headers(self) -> dict[str, Any]:
        custom_headers = self._build_default_headers()
        custom_headers["User-Agent"] = self._CHROME_UA
        return custom_headers

    # ------------------------------------------------------------------
    # Block detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_blocked(page_url: str) -> bool:
        """Return *True* if the current URL indicates ML blocked us."""
        return "account-verification" in page_url or "login" in page_url

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def _extract_links(self, page) -> list[str]:
        """Extract product URLs from a rendered search results page."""
        raw_links = await page.query_selector_all(".poly-component__title")
        hrefs = []
        for el in raw_links:
            href = await el.get_attribute("href")
            if href:
                hrefs.append(href)

        links = []
        seen = set()
        for href in hrefs:
            # Skip ML click-tracker URLs
            if "click1.mercadolivre" in href:
                continue
            if href not in seen:
                seen.add(href)
                links.append(href)

        return links

    def _build_search_url(self, search_term: str, offset: int = 0) -> str:
        encoded = quote_plus(search_term)
        if offset == 0:
            return f"{self.BASE_URL}/{encoded}"
        start_from = offset + 1
        return f"{self.BASE_URL}/{encoded}_Desde_{start_from}_NoIndex_True"

    def search(self, search_term: str, max_pages: int = 5) -> list[str]:
        """Synchronous entry point — runs the async search loop."""
        return self._run_async(self._search_async(search_term, max_pages))

    async def _search_async(self, search_term: str, max_pages: int = 5) -> list[str]:
        """Search with automatic proxy rotation on block."""
        last_error: Exception | None = None

        for attempt in range(1, self._MAX_PROXY_RETRIES + 1):
            try:
                return await self._search_with_current_proxy(search_term, max_pages)
            except _ProxyBlockedError as exc:
                last_error = exc
                logger.warning(
                    "ML search blocked (attempt %d/%d) — rotating proxy",
                    attempt,
                    self._MAX_PROXY_RETRIES,
                )
                self._report_proxy_failure(exc.proxy)
                await asyncio.sleep(1.0)

        raise Exception(
            f"ML search failed after {self._MAX_PROXY_RETRIES} proxy attempts: {last_error}"
        )

    async def _search_with_current_proxy(
        self, search_term: str, max_pages: int
    ) -> list[str]:
        all_links: list[str] = []

        await self.start()
        # Get the proxy that _build_context will use (for failure reporting).
        current_proxy = (
            self._proxy_rotator.next_proxy() if self._proxy_rotator else None
        )
        # Build context with that specific proxy.
        context = await self._build_context(proxy=current_proxy)
        page = await context.new_page()
        page.set_default_timeout(self._DEFAULT_TIMEOUT)

        try:
            for page_number in range(1, max_pages + 1):
                search_url = self._build_search_url(search_term, len(all_links))
                logger.debug("ML: loading page %d — %s", page_number, search_url)

                try:
                    await page.goto(
                        search_url,
                        wait_until="domcontentloaded",
                        timeout=30_000,
                    )
                except Exception as e:
                    logger.warning(
                        "ML: page %d failed to load: %s — stopping",
                        page_number,
                        e,
                    )
                    break

                # Detect ML block (302 redirect to login page).
                if self._is_blocked(page.url):
                    raise _ProxyBlockedError(proxy=current_proxy, url=page.url)

                try:
                    await page.wait_for_selector(
                        ".ui-search-layout__item", timeout=10_000
                    )
                except Exception:
                    logger.debug(
                        "ML: no search items on page %d — stopping", page_number
                    )
                    break

                links = await self._extract_links(page)

                if not links:
                    logger.debug("ML: no links on page %d — stopping", page_number)
                    break

                all_links.extend(links)
                logger.debug(
                    "ML: page %d — %d links (total %d)",
                    page_number,
                    len(links),
                    len(all_links),
                )

                # Check if there is a next page
                next_btn = await page.query_selector(
                    "a.andes-pagination__link[title='Seguinte']"
                )
                if not next_btn:
                    logger.debug("ML: no next page button — stopping")
                    break

                # Throttle to avoid detection
                await asyncio.sleep(1.0)
        finally:
            await context.close()
            # Browser kept alive — see _scrape_with_current_proxy note.

        if not all_links:
            raise Exception("No results found")

        return all_links

    # ------------------------------------------------------------------
    # Product detail
    # ------------------------------------------------------------------

    def scrape_data(self, url: str) -> dict[str, Any]:
        """Synchronous entry point — runs the async scrape."""
        return self._run_async(self._scrape_data_async(url))

    async def _scrape_data_async(self, url: str) -> dict[str, Any]:
        """Scrape with automatic proxy rotation on block."""
        last_error: Exception | None = None

        for attempt in range(1, self._MAX_PROXY_RETRIES + 1):
            try:
                return await self._scrape_with_current_proxy(url)
            except _ProxyBlockedError as exc:
                last_error = exc
                logger.warning(
                    "ML scrape blocked (attempt %d/%d) — rotating proxy",
                    attempt,
                    self._MAX_PROXY_RETRIES,
                )
                self._report_proxy_failure(exc.proxy)
                await asyncio.sleep(1.0)

        raise Exception(
            f"ML scrape failed after {self._MAX_PROXY_RETRIES} proxy attempts: {last_error}"
        )

    async def _scrape_with_current_proxy(self, url: str) -> dict[str, Any]:
        await self.start()
        current_proxy = (
            self._proxy_rotator.next_proxy() if self._proxy_rotator else None
        )
        context = await self._build_context(proxy=current_proxy)
        page = await context.new_page()
        page.set_default_timeout(self._DEFAULT_TIMEOUT)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Detect ML block.
            if self._is_blocked(page.url):
                raise _ProxyBlockedError(proxy=current_proxy, url=page.url)

            await page.wait_for_selector("h1.ui-pdp-title", timeout=10_000)

            title = await self._extract_title(page)
            price = await self._extract_price(page)
            description = await self._extract_description(page)
            source_product_code = self._extract_product_code(url)
            is_available = await self._extract_availability(page)
            image_url = await self._extract_image_src(page)
            seller_name = await self._extract_seller(page)
            location = await self._extract_location(page)
        finally:
            await context.close()
            # NOTE: We intentionally do NOT call self.stop() here.
            # The browser is kept alive so that scrape_batch (and other
            # callers that invoke scrape_data() in a loop) can reuse it
            # across multiple URLs instead of paying the ~2 s cost of
            # spawning a fresh Chromium process for every single request.
            # The browser is cleaned up by stop_sync() in the task's
            # finally block or by explicit stop() calls.

        return {
            "url": url,
            "title": title,
            "price": price,
            "description": description,
            "source_product_code": source_product_code,
            "city": location,
            "state": "not found",
            "seller_name": seller_name,
            "is_available": is_available,
            "image_urls": image_url or "",
            "source_metadata": {},
        }

    async def _extract_title(self, page) -> str:
        el = await page.query_selector("h1.ui-pdp-title")
        return (await el.inner_text()).strip() if el else ""

    async def _extract_price(self, page) -> str:
        meta = await page.query_selector('meta[itemprop="price"]')
        if meta:
            return await meta.get_attribute("content") or ""
        fraction = await page.query_selector(".andes-money-amount__fraction")
        return (await fraction.inner_text()).strip() if fraction else ""

    async def _extract_description(self, page) -> str:
        el = await page.query_selector("p.ui-pdp-description__content")
        return (await el.inner_text()).strip() if el else ""

    async def _extract_availability(self, page) -> bool:
        el = await page.query_selector(".ui-pdp-stock-information__title")
        if el:
            text = (await el.inner_text()).strip().lower()
            if "disponível" in text or "disponivel" in text:
                return True
        price = await self._extract_price(page)
        return bool(price)

    @staticmethod
    def _extract_product_code(url: str) -> str:
        """Extract the ML product ID (e.g. MLB123456789) from the URL."""
        match = re.search(r"(MLB\d+)", url)
        if match:
            return f"ML - {match.group(1)}"
        fragment = urlparse(url).fragment
        params = parse_qs(fragment)
        wid = params.get("wid", [None])[0]
        if wid:
            return f"ML - {wid}"
        path_segment = urlparse(url).path.rstrip("/").split("/")[-1]
        return f"ML - {path_segment}" if path_segment else "ML - unknown"

    async def _extract_image_src(self, page) -> str | None:
        el = await page.query_selector("img.ui-pdp-image.ui-pdp-gallery__figure__image")
        if el:
            return await el.get_attribute("src")
        el = await page.query_selector("figure.ui-pdp-gallery__figure img")
        if el:
            return await el.get_attribute("src")
        return None

    async def _extract_seller(self, page) -> str:
        el = await page.query_selector(".ui-pdp-seller__link-trigger-button")
        if el:
            return (await el.inner_text()).strip()
        el = await page.query_selector(".ui-pdp-seller__header__title")
        if el:
            return (await el.inner_text()).strip()
        return "not found"

    async def _extract_location(self, page) -> str:
        el = await page.query_selector(".ui-pdp-media__body p")
        if el:
            return (await el.inner_text()).strip()
        return "not found"

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_data(self, product: dict) -> dict:
        data = self.scrape_data(product["url"])
        return {**product, **data}

    def __str__(self):
        return "Mercado Livre Scraper"
