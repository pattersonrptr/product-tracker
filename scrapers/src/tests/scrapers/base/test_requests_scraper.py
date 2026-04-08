"""
Tests for src/product_scrapers/scrapers/base/requests_scraper.py.

Strategy: patch cloudscraper.create_scraper so no real HTTP is made; the
session object is replaced by a MagicMock whose .get() we control.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.scrapers.base.requests_scraper import RequestScraper

# ---------------------------------------------------------------------------
# Concrete subclass for testing the ABC
# ---------------------------------------------------------------------------


class _ConcreteRequestScraper(RequestScraper):
    """Minimal concrete implementation used only in tests."""

    def headers(self) -> dict:
        return {"User-Agent": "test"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_good_response(url: str = "http://example.com"):
    resp = MagicMock(spec=requests.Response)
    resp.url = url
    resp.raise_for_status = MagicMock()  # does not raise
    return resp


def _make_error_response():
    resp = MagicMock(spec=requests.Response)
    resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
    return resp


# ---------------------------------------------------------------------------
# __init__ / cloudscraper
# ---------------------------------------------------------------------------


@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_init_creates_cloudscraper_session(mock_create_scraper):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session

    scraper = _ConcreteRequestScraper()

    mock_create_scraper.assert_called_once()
    assert scraper._session is mock_session


# ---------------------------------------------------------------------------
# __init__ / USE_CLOUDSCRAPER = False
# ---------------------------------------------------------------------------


class _PlainRequestScraper(RequestScraper):
    """Subclass that opts out of cloudscraper."""

    USE_CLOUDSCRAPER = False

    def headers(self) -> dict:
        return {"User-Agent": "plain"}


@patch("src.scrapers.base.requests_scraper.requests.Session")
def test_init_creates_plain_session_when_cloudscraper_disabled(mock_session_cls):
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    scraper = _PlainRequestScraper()

    mock_session_cls.assert_called_once()
    assert scraper._session is mock_session


# ---------------------------------------------------------------------------
# retry_request — happy path
# ---------------------------------------------------------------------------


@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_returns_response_on_first_attempt(mock_create_scraper):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session

    resp = _make_good_response()
    mock_session.get.return_value = resp

    scraper = _ConcreteRequestScraper()
    result = scraper.retry_request("http://example.com")

    assert result is resp
    # When headers is not passed, defaults to self.headers()
    mock_session.get.assert_called_once_with(
        "http://example.com",
        headers={"User-Agent": "test"},
        params={},
        allow_redirects=True,
    )


@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_passes_headers_and_params(mock_create_scraper):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session
    mock_session.get.return_value = _make_good_response()

    scraper = _ConcreteRequestScraper()
    scraper.retry_request(
        "http://example.com",
        headers={"X-Test": "1"},
        params={"q": "book"},
    )

    mock_session.get.assert_called_once_with(
        "http://example.com",
        headers={"X-Test": "1"},
        params={"q": "book"},
        allow_redirects=True,
    )


# ---------------------------------------------------------------------------
# retry_request — retries on RequestException
# ---------------------------------------------------------------------------


@patch("src.scrapers.base.requests_scraper.time.sleep")
@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_retries_on_connection_error_then_succeeds(
    mock_create_scraper, mock_sleep
):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session

    good_resp = _make_good_response()
    mock_session.get.side_effect = [
        requests.exceptions.ConnectionError("timeout"),
        good_resp,
    ]

    scraper = _ConcreteRequestScraper()
    result = scraper.retry_request("http://example.com", max_retries=3)

    assert result is good_resp
    assert mock_session.get.call_count == 2
    mock_sleep.assert_called_once()  # slept once between attempts


@patch("src.scrapers.base.requests_scraper.time.sleep")
@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_returns_none_after_all_retries_exhausted(
    mock_create_scraper, mock_sleep
):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session
    mock_session.get.side_effect = requests.exceptions.ConnectionError("no route")

    scraper = _ConcreteRequestScraper()
    result = scraper.retry_request("http://example.com", max_retries=2)

    assert result is None
    # Called max_retries + 1 times (initial + retries)
    assert mock_session.get.call_count == 3


# ---------------------------------------------------------------------------
# retry_request — raises_for_status triggers retry
# ---------------------------------------------------------------------------


@patch("src.scrapers.base.requests_scraper.time.sleep")
@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_retries_on_http_error(mock_create_scraper, mock_sleep):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session

    good_resp = _make_good_response()
    mock_session.get.side_effect = [
        requests.exceptions.HTTPError("500"),
        good_resp,
    ]

    scraper = _ConcreteRequestScraper()
    result = scraper.retry_request("http://example.com", max_retries=3)

    assert result is good_resp


# ---------------------------------------------------------------------------
# retry_request — unexpected exception returns None immediately
# ---------------------------------------------------------------------------


@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_returns_none_on_unexpected_exception(mock_create_scraper):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session
    mock_session.get.side_effect = ValueError("unexpected")

    scraper = _ConcreteRequestScraper()
    result = scraper.retry_request("http://example.com", max_retries=3)

    assert result is None
    # Should only call once — unexpected exceptions are not retried
    mock_session.get.assert_called_once()


# ---------------------------------------------------------------------------
# retry_request — backoff_factor influences sleep duration
# ---------------------------------------------------------------------------


@patch("src.scrapers.base.requests_scraper.time.sleep")
@patch("src.scrapers.base.requests_scraper.cloudscraper.create_scraper")
def test_retry_request_exponential_backoff(mock_create_scraper, mock_sleep):
    mock_session = MagicMock()
    mock_create_scraper.return_value = mock_session

    good_resp = _make_good_response()
    mock_session.get.side_effect = [
        requests.exceptions.ConnectionError("fail"),
        requests.exceptions.ConnectionError("fail"),
        good_resp,
    ]

    scraper = _ConcreteRequestScraper()
    result = scraper.retry_request(
        "http://example.com", max_retries=3, backoff_factor=2.0
    )

    assert result is good_resp
    # sleep called twice: after attempt 0 and attempt 1
    assert mock_sleep.call_count == 2
    # backoff: 2^0 * 1 = 1.0 then 2^1 * 1 = 2.0
    sleep_times = [c.args[0] for c in mock_sleep.call_args_list]
    assert sleep_times[0] == pytest.approx(1.0)
    assert sleep_times[1] == pytest.approx(2.0)
