"""
Tests for src/scrapers/base/playwright_scraper.py.

Strategy: mock playwright.async_api so no real browser is launched.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.proxy_rotator import FreeProxyRotator, PaidProxyRotator
from src.scrapers.base.playwright_scraper import PlaywrightScraper

# ---------------------------------------------------------------------------
# Concrete subclass for testing
# ---------------------------------------------------------------------------


class ConcretePlaywrightScraper(PlaywrightScraper):
    """Minimal concrete subclass to test the ABC."""

    def headers(self):
        return {
            "Accept": "text/html",
            "User-Agent": "Test-UA/1.0",
        }


class ProxiedPlaywrightScraper(PlaywrightScraper):
    """Subclass with proxy support enabled for testing."""

    _USE_PROXY = True

    def headers(self):
        return {
            "Accept": "text/html",
            "User-Agent": "Test-UA/1.0",
        }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scraper():
    return ConcretePlaywrightScraper()


def _make_mock_browser():
    """Create a fully async-capable mock browser with nested context/page."""
    browser = AsyncMock()
    browser.is_connected.return_value = True

    context = AsyncMock()
    context.add_init_script = AsyncMock()
    page = AsyncMock()
    page.set_default_timeout = MagicMock()
    page.goto = AsyncMock()
    context.new_page = AsyncMock(return_value=page)

    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()
    return browser, context, page


@pytest.fixture
def mock_async_playwright():
    """Patch async_playwright to return mocked objects."""
    browser, context, page = _make_mock_browser()

    pw_instance = MagicMock()
    pw_instance.chromium.launch = AsyncMock(return_value=browser)

    with patch("src.scrapers.base.playwright_scraper.async_playwright") as mock_ap:
        mock_ap.return_value.start = AsyncMock(return_value=pw_instance)
        yield {
            "async_playwright": mock_ap,
            "pw_instance": pw_instance,
            "browser": browser,
            "context": context,
            "page": page,
        }


# ---------------------------------------------------------------------------
# start / stop (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_launches_chromium(scraper, mock_async_playwright):
    await scraper.start()
    pw = mock_async_playwright["pw_instance"]
    pw.chromium.launch.assert_called_once_with(headless=True)
    assert scraper._browser is not None


@pytest.mark.asyncio
async def test_start_is_idempotent(scraper, mock_async_playwright):
    """Calling start() twice doesn't launch a second browser."""
    await scraper.start()
    await scraper.start()  # Already connected
    pw = mock_async_playwright["pw_instance"]
    pw.chromium.launch.assert_called_once()


@pytest.mark.asyncio
async def test_stop_closes_browser_and_playwright(scraper, mock_async_playwright):
    browser, context, page = _make_mock_browser()
    playwright_inst = MagicMock()
    playwright_inst.stop = AsyncMock()
    scraper._browser = browser
    scraper._playwright = playwright_inst

    await scraper.stop()

    browser.close.assert_called_once()
    playwright_inst.stop.assert_called_once()
    assert scraper._browser is None
    assert scraper._playwright is None


@pytest.mark.asyncio
async def test_stop_when_not_started(scraper):
    """stop() is safe to call when no browser is running."""
    await scraper.stop()  # Should not raise


# ---------------------------------------------------------------------------
# _build_context (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_context_uses_headers(scraper, mock_async_playwright):
    browser, context, page = _make_mock_browser()
    scraper._browser = browser

    await scraper._build_context()

    browser.new_context.assert_called_once()
    call_kwargs = browser.new_context.call_args.kwargs
    assert call_kwargs["user_agent"] == "Test-UA/1.0"
    assert call_kwargs["locale"] == "pt-BR"
    assert call_kwargs["timezone_id"] == "America/Sao_Paulo"
    assert call_kwargs["viewport"] == {"width": 1366, "height": 768}
    assert "Accept" in call_kwargs["extra_http_headers"]
    assert "User-Agent" not in call_kwargs["extra_http_headers"]
    assert context.add_init_script.call_count == len(
        ConcretePlaywrightScraper._STEALTH_SCRIPTS
    )


@pytest.mark.asyncio
async def test_build_context_without_user_agent(mock_async_playwright):
    """When headers() has no User-Agent, user_agent kwarg should be None."""

    class NoUAScraper(PlaywrightScraper):
        def headers(self):
            return {"Accept": "text/html"}

    browser, context, page = _make_mock_browser()
    s = NoUAScraper()
    s._browser = browser

    await s._build_context()

    call_kwargs = browser.new_context.call_args.kwargs
    assert call_kwargs["user_agent"] is None


# ---------------------------------------------------------------------------
# new_page (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_new_page_returns_context_and_page(scraper, mock_async_playwright):
    browser, context, page = _make_mock_browser()
    scraper._browser = browser

    ctx, p = await scraper.new_page()

    assert ctx is context
    assert p is page
    p.set_default_timeout.assert_called_once_with(30_000)


@pytest.mark.asyncio
async def test_new_page_calls_start(scraper, mock_async_playwright):
    """new_page auto-starts the browser if needed."""
    browser, context, page = _make_mock_browser()
    scraper._browser = browser
    # Disconnect so start() is triggered
    scraper._browser = None

    ctx, p = await scraper.new_page()

    mock_async_playwright["pw_instance"].chromium.launch.assert_called()


# ---------------------------------------------------------------------------
# fetch_page (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_page_navigates_and_returns_page(scraper, mock_async_playwright):
    browser, context, page = _make_mock_browser()
    scraper._browser = browser

    ctx, p = await scraper.fetch_page("https://example.com")

    page.goto.assert_called_once_with("https://example.com", wait_until="networkidle")
    assert ctx is context
    assert p is page


@pytest.mark.asyncio
async def test_fetch_page_custom_wait_until(scraper, mock_async_playwright):
    browser, context, page = _make_mock_browser()
    scraper._browser = browser

    await scraper.fetch_page("https://example.com", wait_until="domcontentloaded")

    page.goto.assert_called_once_with(
        "https://example.com", wait_until="domcontentloaded"
    )


# ---------------------------------------------------------------------------
# Sync wrappers
# ---------------------------------------------------------------------------


def test_start_sync_launches_browser(scraper, mock_async_playwright):
    """start_sync() should launch the browser synchronously."""
    scraper.start_sync()
    pw = mock_async_playwright["pw_instance"]
    pw.chromium.launch.assert_called_once()


def test_stop_sync_closes_browser(scraper, mock_async_playwright):
    """stop_sync() should close the browser synchronously."""
    browser, context, page = _make_mock_browser()
    scraper._browser = browser
    scraper._playwright = MagicMock()
    scraper._playwright.stop = AsyncMock()

    scraper.stop_sync()

    browser.close.assert_called_once()


def test_fetch_page_sync_returns_context_and_page(scraper, mock_async_playwright):
    """fetch_page_sync() should return context and page synchronously."""
    browser, context, page = _make_mock_browser()
    scraper._browser = browser

    ctx, p = scraper.fetch_page_sync("https://example.com")

    assert ctx is context
    assert p is page
    page.goto.assert_called_once()


# ---------------------------------------------------------------------------
# Context manager (sync)
# ---------------------------------------------------------------------------


def test_context_manager(scraper, mock_async_playwright):
    browser, context, page = _make_mock_browser()
    scraper._browser = browser
    scraper._playwright = MagicMock()
    scraper._playwright.stop = AsyncMock()

    with scraper as s:
        assert s is scraper

    browser.close.assert_called_once()


# ---------------------------------------------------------------------------
# Class attributes
# ---------------------------------------------------------------------------


def test_default_headless_is_true():
    assert ConcretePlaywrightScraper._HEADLESS is True


def test_default_timeout():
    assert ConcretePlaywrightScraper._DEFAULT_TIMEOUT == 30_000


def test_use_proxy_default_is_false():
    assert ConcretePlaywrightScraper._USE_PROXY is False


# ---------------------------------------------------------------------------
# Proxy support
# ---------------------------------------------------------------------------


class TestProxyIntegration:
    """Verify that proxy rotator is wired into context creation."""

    def test_no_proxy_when_use_proxy_false(self):
        """Scrapers without _USE_PROXY should have no proxy rotator."""
        scraper = ConcretePlaywrightScraper()
        assert scraper._proxy_rotator is None

    @patch.dict(
        "os.environ",
        {
            "PROXY_ENABLED": "true",
            "PROXY_SERVER": "http://proxy:8080",
            "PROXY_USERNAME": "user",
            "PROXY_PASSWORD": "pass",
        },
    )
    def test_no_proxy_when_use_proxy_false_even_if_env_set(self):
        """Even with env vars set, _USE_PROXY=False means no proxy."""
        scraper = ConcretePlaywrightScraper()
        assert scraper._proxy_rotator is None

    @patch.dict(
        "os.environ",
        {
            "PROXY_ENABLED": "true",
            "PROXY_SERVER": "http://proxy:8080",
            "PROXY_USERNAME": "user",
            "PROXY_PASSWORD": "pass",
        },
    )
    def test_paid_proxy_loaded_when_use_proxy_true(self):
        """Scrapers with _USE_PROXY=True + env vars get PaidProxyRotator."""
        scraper = ProxiedPlaywrightScraper()
        assert scraper._proxy_rotator is not None
        assert isinstance(scraper._proxy_rotator, PaidProxyRotator)

    @patch.dict("os.environ", {}, clear=True)
    def test_free_proxy_fallback_when_no_env(self):
        """_USE_PROXY=True but no paid env vars → FreeProxyRotator."""
        scraper = ProxiedPlaywrightScraper()
        assert scraper._proxy_rotator is not None
        assert isinstance(scraper._proxy_rotator, FreeProxyRotator)

    @pytest.mark.asyncio
    @patch.dict(
        "os.environ",
        {
            "PROXY_ENABLED": "true",
            "PROXY_SERVER": "http://proxy:8080",
            "PROXY_USERNAME": "user",
            "PROXY_PASSWORD": "pass",
        },
    )
    async def test_build_context_passes_paid_proxy(self):
        """_build_context() should pass proxy kwarg from paid rotator."""
        browser, context, page = _make_mock_browser()
        scraper = ProxiedPlaywrightScraper()
        scraper._browser = browser

        await scraper._build_context()

        call_kwargs = browser.new_context.call_args.kwargs
        assert "proxy" in call_kwargs
        assert call_kwargs["proxy"]["server"] == "http://proxy:8080"
        assert call_kwargs["proxy"]["username"] == "user"
        assert call_kwargs["proxy"]["password"] == "pass"

    @pytest.mark.asyncio
    async def test_build_context_no_proxy_kwarg_when_disabled(self):
        """_build_context() should NOT pass proxy kwarg when not configured."""
        browser, context, page = _make_mock_browser()
        scraper = ConcretePlaywrightScraper()
        scraper._browser = browser

        await scraper._build_context()

        call_kwargs = browser.new_context.call_args.kwargs
        assert "proxy" not in call_kwargs

    @pytest.mark.asyncio
    async def test_build_context_accepts_explicit_proxy(self):
        """_build_context(proxy=...) should use the explicit proxy dict."""
        browser, context, page = _make_mock_browser()
        scraper = ConcretePlaywrightScraper()
        scraper._browser = browser

        explicit_proxy = {"server": "socks5://my-proxy:1080"}
        await scraper._build_context(proxy=explicit_proxy)

        call_kwargs = browser.new_context.call_args.kwargs
        assert call_kwargs["proxy"] == {"server": "socks5://my-proxy:1080"}
