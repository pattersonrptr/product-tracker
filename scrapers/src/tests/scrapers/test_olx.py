"""
Tests for src/product_scrapers/scrapers/olx.py.

Strategy: patch cloudscraper.create_scraper and RotatingUserAgentMixin._load_user_agents
so no real HTTP or file I/O happens.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from src.scrapers.olx import OLXScraper

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _build_olx_html(ads: list[dict]) -> str:
    """Build minimal __NEXT_DATA__ HTML for OLX search page."""
    data = {"props": {"pageProps": {"ads": ads}}}
    return f'<html><body><script id="__NEXT_DATA__">{json.dumps(data)}</script></body></html>'


def _build_product_html(
    subject="Cool Book",
    list_id="123",
    price_value="R$50,00",
    body="Great condition",
    seller_name="João",
    city="São Paulo",
    uf="SP",
    images=None,
) -> bytes:
    """Build minimal initial-data HTML for an OLX product page."""
    if images is None:
        images = [{"original": "https://img.olx.com.br/1.jpg"}]
    ad = {
        "subject": subject,
        "listId": list_id,
        "priceValue": price_value,
        "body": body,
        "user": {"name": seller_name},
        "location": {"municipality": city, "uf": uf},
        "images": images,
    }
    import html

    data_json = html.escape(json.dumps({"ad": ad}))
    return f'<html><body><script id="initial-data" data-json="{data_json}"></script></body></html>'.encode()


def _mock_response(status_code: int = 200, text: str = "", content: bytes = b""):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    resp.content = content
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture
def scraper():
    with patch.object(OLXScraper, "_load_user_agents", return_value=[]):
        s = OLXScraper()
    return s


# ---------------------------------------------------------------------------
# __init__ / BASE_URL
# ---------------------------------------------------------------------------


def test_olx_scraper_base_url(scraper):
    assert scraper.BASE_URL == "https://www.olx.com.br/brasil"


def test_str(scraper):
    assert str(scraper) == "OLX Scraper"


# ---------------------------------------------------------------------------
# _build_default_headers
# ---------------------------------------------------------------------------


def test_build_default_headers_returns_expected_keys(scraper):
    headers = OLXScraper._build_default_headers()
    assert "Accept" in headers
    assert "Accept-Language" in headers


# ---------------------------------------------------------------------------
# headers()
# ---------------------------------------------------------------------------


def test_headers_without_user_agent(scraper):
    # No user agents loaded
    result = scraper.headers()
    assert "Accept" in result
    assert "User-Agent" not in result


def test_headers_with_user_agent(scraper):
    scraper._user_agents = ["Mozilla/5.0 Test"]
    result = scraper.headers()
    assert result["User-Agent"] == "Mozilla/5.0 Test"


# ---------------------------------------------------------------------------
# _build_search_url
# ---------------------------------------------------------------------------


def test_build_search_url_page_1(scraper):
    url = scraper._build_search_url("notebook", 1)
    assert "notebook" in url
    assert "&o=1" in url


def test_build_search_url_page_3(scraper):
    url = scraper._build_search_url("cadeira", 3)
    assert "&o=3" in url


def test_build_search_url_encodes_spaces(scraper):
    url = scraper._build_search_url("notebook dell", 1)
    assert " " not in url


# ---------------------------------------------------------------------------
# _extract_links
# ---------------------------------------------------------------------------


def test_extract_links_returns_urls(scraper):
    ads = [{"url": "https://olx.com/a"}, {"url": "https://olx.com/b"}]
    html_content = _build_olx_html(ads)
    links = scraper._extract_links(html_content)
    assert links == ["https://olx.com/a", "https://olx.com/b"]


def test_extract_links_deduplicates(scraper):
    ads = [{"url": "https://olx.com/a"}, {"url": "https://olx.com/a"}]
    html_content = _build_olx_html(ads)
    links = scraper._extract_links(html_content)
    assert links == ["https://olx.com/a"]


def test_extract_links_skips_ad_without_url(scraper):
    ads = [{"url": "https://olx.com/a"}, {"title": "No URL ad"}]
    html_content = _build_olx_html(ads)
    links = scraper._extract_links(html_content)
    assert links == ["https://olx.com/a"]


def test_extract_links_raises_when_no_next_data(scraper):
    with pytest.raises(Exception, match="No data found"):
        scraper._extract_links("<html><body>empty</body></html>")


def test_extract_links_raises_when_no_ads_data(scraper):
    data = {"props": {"pageProps": {}}}
    html_content = f'<html><body><script id="__NEXT_DATA__">{json.dumps(data)}</script></body></html>'
    with pytest.raises(Exception, match="No ads data found"):
        scraper._extract_links(html_content)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@patch.object(OLXScraper, "retry_request")
def test_search_single_page(mock_retry, scraper):
    ads = [{"url": "https://olx.com/a"}, {"url": "https://olx.com/b"}]
    html_content = _build_olx_html(ads)

    # First page has links; second page returns empty → stop
    page1_resp = _mock_response(text=html_content)
    page2_resp = _mock_response(text="<html></html>")  # will raise No data found

    mock_retry.side_effect = [page1_resp, page2_resp]

    result = scraper.search("notebook", max_pages=5)
    assert "https://olx.com/a" in result
    assert "https://olx.com/b" in result


@patch.object(OLXScraper, "retry_request")
def test_search_empty_html_breaks_loop_raises_no_results(mock_retry, scraper):
    mock_retry.return_value = _mock_response(text="")
    with pytest.raises(Exception, match="No results found"):
        scraper.search("notebook", max_pages=5)


@patch.object(OLXScraper, "retry_request")
def test_search_raises_when_no_results(mock_retry, scraper):
    mock_retry.return_value = _mock_response(text="<html><body></body></html>")
    # _extract_links raises → caught → break → results empty → Exception
    with pytest.raises(Exception, match="No results found"):
        scraper.search("nothing", max_pages=1)


# ---------------------------------------------------------------------------
# _extract_json_data
# ---------------------------------------------------------------------------


def test_extract_json_data_returns_ad(scraper):
    html_bytes = _build_product_html(
        subject="Book", list_id="42", price_value="R$30,00"
    )
    soup = BeautifulSoup(html_bytes, "html.parser")
    data = scraper._extract_json_data(soup)
    assert data["subject"] == "Book"
    assert data["listId"] == "42"


def test_extract_json_data_returns_empty_when_no_script(scraper):
    soup = BeautifulSoup("<html></html>", "html.parser")
    data = scraper._extract_json_data(soup)
    assert data == {}


# ---------------------------------------------------------------------------
# scrape_data
# ---------------------------------------------------------------------------


@patch.object(OLXScraper, "retry_request")
def test_scrape_data_returns_expected_fields(mock_retry, scraper):
    html_bytes = _build_product_html(
        subject="Old Bike",
        list_id="777",
        price_value="R$1.200,00",
        body="Ótimo estado",
        seller_name="Maria",
        city="Curitiba",
        uf="PR",
    )
    mock_retry.return_value = _mock_response(content=html_bytes)

    result = scraper.scrape_data("https://olx.com/item/777")
    assert result["url"] == "https://olx.com/item/777"
    assert result["title"] == "Old Bike"
    assert result["description"] == "Ótimo estado"
    assert result["seller_name"] == "Maria"
    assert result["city"] == "Curitiba"
    assert result["state"] == "PR"
    assert result["source_product_code"] == "OLX - 777"
    assert result["image_urls"] == "https://img.olx.com.br/1.jpg"
    assert result["is_available"] is True  # price is truthy


@patch.object(OLXScraper, "retry_request")
def test_scrape_data_no_price_is_unavailable(mock_retry, scraper):
    html_bytes = _build_product_html(price_value="")
    mock_retry.return_value = _mock_response(content=html_bytes)

    result = scraper.scrape_data("https://olx.com/item/123")
    assert result["is_available"] is False


@patch.object(OLXScraper, "retry_request")
def test_scrape_data_no_images(mock_retry, scraper):
    html_bytes = _build_product_html(images=[])
    mock_retry.return_value = _mock_response(content=html_bytes)

    result = scraper.scrape_data("https://olx.com/item/123")
    assert result["image_urls"] == ""


# ---------------------------------------------------------------------------
# update_data
# ---------------------------------------------------------------------------


@patch.object(OLXScraper, "scrape_data")
def test_update_data_merges_and_preserves_id(mock_scrape, scraper):
    mock_scrape.return_value = {
        "url": "https://olx.com/a",
        "title": "Updated Title",
        "price": "200",
        "is_available": True,
    }
    product = {"id": "99", "url": "https://olx.com/a", "title": "Old Title"}
    result = scraper.update_data(product)

    assert result["id"] == "99"
    assert result["title"] == "Updated Title"
    mock_scrape.assert_called_once_with("https://olx.com/a")


@patch.object(OLXScraper, "scrape_data")
def test_update_data_without_id(mock_scrape, scraper):
    """If product has no 'id', update_data still works."""
    mock_scrape.return_value = {"url": "https://olx.com/a", "title": "New"}
    product = {"url": "https://olx.com/a"}
    result = scraper.update_data(product)
    assert "id" not in result
    assert result["title"] == "New"
