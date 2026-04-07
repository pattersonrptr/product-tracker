import logging
from abc import ABC, abstractmethod
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

logger = logging.getLogger(__name__)


class PlaywrightScraper(ABC):
    """Base class providing a headless Chromium browser for sites that
    require JavaScript rendering (CSR/SSR hydration).

    Manages browser lifecycle: ``start()`` / ``stop()`` control the
    Chromium process.  ``new_page()`` creates stealth-configured pages
    with random viewport and locale.

    Subclasses must implement ``headers()`` which returns default HTTP
    headers used when creating browser contexts.
    """

    _HEADLESS: bool = True
    _DEFAULT_TIMEOUT: int = 30_000  # 30 seconds

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._playwright = None
        self._browser: Browser | None = None

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Launch the Chromium browser."""
        if self._browser and self._browser.is_connected():
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._HEADLESS)
        logger.debug("Playwright browser started (headless=%s)", self._HEADLESS)

    def stop(self) -> None:
        """Close the browser and free resources."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        logger.debug("Playwright browser stopped")

    # ------------------------------------------------------------------
    # Page helpers
    # ------------------------------------------------------------------

    @abstractmethod
    def headers(self) -> dict[str, Any]:
        raise NotImplementedError

    # JavaScript snippets injected into every new context to reduce the
    # chance of being flagged as an automated browser.
    _STEALTH_SCRIPTS: list[str] = [
        # Hide the ``navigator.webdriver`` flag that headless Chromium sets.
        'Object.defineProperty(navigator, "webdriver", { get: () => undefined });',
    ]

    def _build_context(self) -> BrowserContext:
        """Create a new browser context with stealth-like settings."""
        headers = self.headers()
        user_agent = headers.pop("User-Agent", None)

        context = self._browser.new_context(
            user_agent=user_agent,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            extra_http_headers=headers,
            viewport={"width": 1366, "height": 768},
        )

        for script in self._STEALTH_SCRIPTS:
            context.add_init_script(script)

        return context

    def new_page(self) -> tuple[BrowserContext, Page]:
        """Create a new context + page pair.

        Returns ``(context, page)`` so the caller can close the context
        after use, which also closes all pages within it.
        """
        self.start()
        context = self._build_context()
        page = context.new_page()
        page.set_default_timeout(self._DEFAULT_TIMEOUT)
        return context, page

    def fetch_page(self, url: str, wait_until: str = "networkidle") -> Page:
        """Navigate to *url* and return the rendered page.

        The caller is responsible for closing the page's context via
        ``page.context.close()`` when done.
        """
        context, page = self.new_page()
        page.goto(url, wait_until=wait_until)
        return page

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
