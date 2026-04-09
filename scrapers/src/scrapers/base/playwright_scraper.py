import asyncio
import contextlib
import logging
import threading
from abc import ABC, abstractmethod
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.config.proxy_rotator import (
    FreeProxyRotator,
    PaidProxyRotator,
    get_proxy_rotator,
)

logger = logging.getLogger(__name__)


class PlaywrightScraper(ABC):
    """Base class providing a headless Chromium browser for sites that
    require JavaScript rendering (CSR/SSR hydration).

    Uses Playwright **async** API to avoid conflicts with Celery's
    asyncio event loop.

    Manages browser lifecycle: ``start()`` / ``stop()`` control the
    Chromium process.  ``new_page()`` creates stealth-configured pages
    with random viewport and locale.

    Subclasses must implement ``headers()`` which returns default HTTP
    headers used when creating browser contexts.
    """

    _HEADLESS: bool = True
    _DEFAULT_TIMEOUT: int = 30_000  # 30 seconds

    # Subclasses that need proxy routing (e.g. MercadoLivreScraper) set
    # this to ``True``.  When enabled, the scraper first checks for a
    # paid proxy (PROXY_* env vars); if none is configured, it falls
    # back to free SOCKS5 proxy rotation.
    _USE_PROXY: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._playwright = None
        self._browser: Browser | None = None
        self._proxy_rotator: PaidProxyRotator | FreeProxyRotator | None = (
            get_proxy_rotator() if self._USE_PROXY else None
        )

    # ------------------------------------------------------------------
    # Browser lifecycle (async)
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Launch the Chromium browser (async)."""
        if self._browser and self._browser.is_connected():
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._HEADLESS)
        logger.debug("Playwright browser started (headless=%s)", self._HEADLESS)

    async def stop(self) -> None:
        """Close the browser and free resources (async)."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("Playwright browser stopped")

    # ------------------------------------------------------------------
    # Page helpers (async)
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

    async def _build_context(
        self, proxy: dict[str, Any] | None = None
    ) -> BrowserContext:
        """Create a new browser context with stealth-like settings.

        Parameters
        ----------
        proxy:
            An explicit Playwright-compatible proxy dict.  When *None*
            and :attr:`_USE_PROXY` is ``True``, the next proxy from the
            rotator is used automatically.
        """
        headers = self.headers()
        user_agent = headers.pop("User-Agent", None)

        kwargs: dict[str, Any] = {
            "user_agent": user_agent,
            "locale": "pt-BR",
            "timezone_id": "America/Sao_Paulo",
            "extra_http_headers": headers,
            "viewport": {"width": 1366, "height": 768},
        }

        # Resolve which proxy to use (explicit > rotator > none).
        effective_proxy = proxy
        if effective_proxy is None and self._proxy_rotator is not None:
            effective_proxy = self._proxy_rotator.next_proxy()

        if effective_proxy:
            kwargs["proxy"] = effective_proxy
            logger.debug("Proxy applied to context: %s", effective_proxy.get("server"))

        context = await self._browser.new_context(**kwargs)

        for script in self._STEALTH_SCRIPTS:
            await context.add_init_script(script)

        return context

    def _report_proxy_failure(self, proxy: dict[str, Any] | None) -> None:
        """Tell the rotator that *proxy* is dead so it won't be reused."""
        if proxy and self._proxy_rotator:
            self._proxy_rotator.report_failure(proxy)

    async def new_page(self) -> tuple[BrowserContext, Page]:
        """Create a new context + page pair.

        Returns ``(context, page)`` so the caller can close the context
        after use, which also closes all pages within it.
        """
        await self.start()
        context = await self._build_context()
        page = await context.new_page()
        page.set_default_timeout(self._DEFAULT_TIMEOUT)
        return context, page

    async def fetch_page(
        self, url: str, wait_until: str = "networkidle"
    ) -> tuple[BrowserContext, Page]:
        """Navigate to *url* and return ``(context, page)``.

        The caller is responsible for closing the context when done,
        which also closes all pages within it.
        """
        context, page = await self.new_page()
        await page.goto(url, wait_until=wait_until)
        return context, page

    # ------------------------------------------------------------------
    # Sync wrappers — for use by sync callers (e.g. Celery tasks).
    # ------------------------------------------------------------------

    # A dedicated event loop running in a background thread.  This loop
    # persists for the lifetime of the scraper instance so that the
    # Playwright browser (which is bound to the loop) survives across
    # multiple ``_run_async`` calls.
    _loop: asyncio.AbstractEventLoop | None = None
    _loop_thread: threading.Thread | None = None
    _loop_lock = threading.Lock()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Return a persistent event loop, creating one if needed."""
        with self._loop_lock:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                self._loop_thread = threading.Thread(
                    target=self._loop.run_forever, daemon=True
                )
                self._loop_thread.start()
            return self._loop

    def _run_async(self, coro):
        """Run an async coroutine on the persistent background loop.

        This keeps the Playwright browser alive across sequential calls
        (e.g. when processing a batch of URLs) because the event loop
        is **not** torn down between invocations.
        """
        loop = self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    def _shutdown_loop(self) -> None:
        """Stop the background event loop and join its thread."""
        with self._loop_lock:
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
                if self._loop_thread:
                    self._loop_thread.join(timeout=10)
                self._loop.close()
            self._loop = None
            self._loop_thread = None

    def start_sync(self) -> None:
        """Synchronous wrapper for ``start()``."""
        self._run_async(self.start())

    def stop_sync(self) -> None:
        """Synchronous wrapper for ``stop()`` + tear down the background loop."""
        self._run_async(self.stop())
        self._shutdown_loop()

    def fetch_page_sync(
        self, url: str, wait_until: str = "networkidle"
    ) -> tuple[BrowserContext, Page]:
        """Synchronous wrapper for ``fetch_page()``.

        Returns ``(context, page)`` so the caller can close the context.
        """

        async def _fetch():
            await self.start()
            context = await self._build_context()
            page = await context.new_page()
            page.set_default_timeout(self._DEFAULT_TIMEOUT)
            await page.goto(url, wait_until=wait_until)
            return context, page

        return self._run_async(_fetch())

    # ------------------------------------------------------------------
    # Context manager (sync)
    # ------------------------------------------------------------------

    def __enter__(self):
        self.start_sync()
        return self

    def __exit__(self, *exc):
        self.stop_sync()

    def __del__(self):
        """Best-effort cleanup if the scraper is garbage-collected."""
        with contextlib.suppress(Exception):
            self._shutdown_loop()
