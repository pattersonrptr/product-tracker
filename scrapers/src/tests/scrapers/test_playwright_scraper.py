"""
Tests for src/scrapers/base/playwright_scraper.py.

Strategy: mock playwright.sync_api so no real browser is launched.
"""

from unittest.mock import MagicMock, patch

import pytest

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scraper():
    return ConcretePlaywrightScraper()


@pytest.fixture
def mock_playwright():
    """Patch sync_playwright to return mocked objects."""
    with patch(
        "src.scrapers.base.playwright_scraper.sync_playwright"
    ) as mock_sp:
        pw_instance = MagicMock()
        browser = MagicMock()
        browser.is_connected.return_value = True
        pw_instance.chromium.launch.return_value = browser
        mock_sp.return_value.start.return_value = pw_instance
        yield {
            "sync_playwright": mock_sp,
            "pw_instance": pw_instance,
            "browser": browser,
        }


# ---------------------------------------------------------------------------
# start / stop
# ---------------------------------------------------------------------------


def test_start_launches_chromium(scraper, mock_playwright):
    scraper.start()
    pw = mock_playwright["pw_instance"]
    pw.chromium.launch.assert_called_once_with(headless=True)
    assert scraper._browser is not None


def test_start_is_idempotent(scraper, mock_playwright):
    """Calling start() twice doesn't launch a second browser."""
    scraper.start()
    scraper.start()  # Already connected
    pw = mock_playwright["pw_instance"]
    pw.chromium.launch.assert_called_once()


def test_stop_closes_browser_and_playwright(scraper, mock_playwright):
    scraper.start()
    browser = mock_playwright["browser"]
    scraper.stop()
    browser.close.assert_called_once()
    assert scraper._browser is None
    assert scraper._playwright is None


def test_stop_when_not_started(scraper):
    """stop() is safe to call when no browser is running."""
    scraper.stop()  # Should not raise


# ---------------------------------------------------------------------------
# _build_context
# ---------------------------------------------------------------------------


def test_build_context_uses_headers(scraper, mock_playwright):
    scraper.start()
    browser = mock_playwright["browser"]
    context_mock = MagicMock()
    browser.new_context.return_value = context_mock

    ctx = scraper._build_context()

    browser.new_context.assert_called_once()
    call_kwargs = browser.new_context.call_args.kwargs
    # User-Agent should be extracted from headers()
    assert call_kwargs["user_agent"] == "Test-UA/1.0"
    assert call_kwargs["locale"] == "pt-BR"
    assert call_kwargs["timezone_id"] == "America/Sao_Paulo"
    assert call_kwargs["viewport"] == {"width": 1366, "height": 768}
    # Accept header should be in extra_http_headers (User-Agent removed)
    assert "Accept" in call_kwargs["extra_http_headers"]
    assert "User-Agent" not in call_kwargs["extra_http_headers"]
    # Stealth scripts should be injected
    assert context_mock.add_init_script.call_count == len(
        ConcretePlaywrightScraper._STEALTH_SCRIPTS
    )


def test_build_context_without_user_agent(mock_playwright):
    """When headers() has no User-Agent, user_agent kwarg should be None."""

    class NoUAScraper(PlaywrightScraper):
        def headers(self):
            return {"Accept": "text/html"}

    s = NoUAScraper()
    s.start()
    browser = mock_playwright["browser"]
    browser.new_context.return_value = MagicMock()

    s._build_context()

    call_kwargs = browser.new_context.call_args.kwargs
    assert call_kwargs["user_agent"] is None


# ---------------------------------------------------------------------------
# new_page
# ---------------------------------------------------------------------------


def test_new_page_returns_context_and_page(scraper, mock_playwright):
    browser = mock_playwright["browser"]
    context_mock = MagicMock()
    page_mock = MagicMock()
    browser.new_context.return_value = context_mock
    context_mock.new_page.return_value = page_mock

    ctx, page = scraper.new_page()

    assert ctx is context_mock
    assert page is page_mock
    page.set_default_timeout.assert_called_once_with(30_000)


def test_new_page_calls_start(scraper, mock_playwright):
    """new_page auto-starts the browser if needed."""
    browser = mock_playwright["browser"]
    browser.is_connected.return_value = False
    browser.new_context.return_value = MagicMock(
        new_page=MagicMock(return_value=MagicMock())
    )

    scraper.new_page()

    mock_playwright["pw_instance"].chromium.launch.assert_called()


# ---------------------------------------------------------------------------
# fetch_page
# ---------------------------------------------------------------------------


def test_fetch_page_navigates_and_returns_page(scraper, mock_playwright):
    browser = mock_playwright["browser"]
    context_mock = MagicMock()
    page_mock = MagicMock()
    browser.new_context.return_value = context_mock
    context_mock.new_page.return_value = page_mock

    page = scraper.fetch_page("https://example.com")

    page_mock.goto.assert_called_once_with(
        "https://example.com", wait_until="networkidle"
    )
    assert page is page_mock


def test_fetch_page_custom_wait_until(scraper, mock_playwright):
    browser = mock_playwright["browser"]
    context_mock = MagicMock()
    page_mock = MagicMock()
    browser.new_context.return_value = context_mock
    context_mock.new_page.return_value = page_mock

    scraper.fetch_page("https://example.com", wait_until="domcontentloaded")

    page_mock.goto.assert_called_once_with(
        "https://example.com", wait_until="domcontentloaded"
    )


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_context_manager(scraper, mock_playwright):
    with scraper as s:
        assert s is scraper
    mock_playwright["browser"].close.assert_called_once()


# ---------------------------------------------------------------------------
# Class attributes
# ---------------------------------------------------------------------------


def test_default_headless_is_true():
    assert ConcretePlaywrightScraper._HEADLESS is True


def test_default_timeout():
    assert ConcretePlaywrightScraper._DEFAULT_TIMEOUT == 30_000
