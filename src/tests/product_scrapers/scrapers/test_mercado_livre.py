"""
Tests for src/product_scrapers/scrapers/mercado_livre.py.

Strategy: patch cloudscraper.create_scraper and RotatingUserAgentMixin._load_user_agents
so no real HTTP or file I/O happens.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from src.product_scrapers.scrapers.mercado_livre import MercadoLivreScraper

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _mock_response(status_code: int = 200, text: str = "", content: bytes = b""):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    resp.content = content
    resp.raise_for_status = MagicMock()
    return resp


def _build_search_html(links: list[str]) -> str:
    """Build minimal HTML matching .poly-component__title-wrapper a selector."""
    items = ""
    for link in links:
        items += f'<div class="poly-component__title-wrapper"><a href="{link}">Product</a></div>'
    # Mix in a click1 tracker link to test filtering
    items += '<div class="poly-component__title-wrapper"><a href="https://click1.mercadolivre.com.br/tracker">Sponsored</a></div>'
    return f"<html><body>{items}</body></html>"


def _build_product_html(
    title: str = "Notebook Dell",
    price: str = "3500.00",
    description: str = "Descrição do produto",
    available: bool = True,
    image_src: str = "https://http2.mlstatic.com/D_NQ_NP_123.jpg",
    product_code_in_url: str = "MLB123456789",
) -> bytes:
    availability_html = (
        '<p class="ui-pdp-stock-information__title">Disponível: 10 unidades</p>'
        if available
        else ""
    )
    image_html = (
        f'<img class="ui-pdp-image ui-pdp-gallery__figure__image" src="{image_src}"/>'
        if image_src
        else ""
    )
    return f"""<html><body>
        <h1 class="ui-pdp-title">{title}</h1>
        <meta itemprop="price" content="{price}"/>
        <p class="ui-pdp-description__content">{description}</p>
        {availability_html}
        {image_html}
    </body></html>""".encode()


@pytest.fixture
def scraper():
    with patch.object(MercadoLivreScraper, "_load_user_agents", return_value=[]):
        s = MercadoLivreScraper()
    return s


# ---------------------------------------------------------------------------
# __init__ / BASE_URL
# ---------------------------------------------------------------------------


def test_base_url(scraper):
    assert scraper.BASE_URL == "https://lista.mercadolivre.com.br"


def test_str(scraper):
    assert str(scraper) == "Mercado Livre Scraper"


# ---------------------------------------------------------------------------
# _build_default_headers
# ---------------------------------------------------------------------------


def test_build_default_headers_keys(scraper):
    headers = MercadoLivreScraper._build_default_headers()
    assert "Accept" in headers
    assert "Accept-Language" in headers


# ---------------------------------------------------------------------------
# headers()
# ---------------------------------------------------------------------------


def test_headers_without_user_agent(scraper):
    result = scraper.headers()
    assert "Accept" in result
    assert "User-Agent" not in result


def test_headers_with_user_agent(scraper):
    scraper._user_agents = ["Mozilla/5.0 ML-Test"]
    result = scraper.headers()
    assert result["User-Agent"] == "Mozilla/5.0 ML-Test"


# ---------------------------------------------------------------------------
# _extract_links
# ---------------------------------------------------------------------------


def test_extract_links_returns_product_links(scraper):
    html = _build_search_html(["https://ml.com/a", "https://ml.com/b"])
    links = scraper._extract_links(html)
    assert "https://ml.com/a" in links
    assert "https://ml.com/b" in links


def test_extract_links_filters_click1_tracker(scraper):
    html = _build_search_html([])
    links = scraper._extract_links(html)
    # The click1 link should NOT be included
    assert not any("click1" in link for link in links)


def test_extract_links_empty_when_no_items(scraper):
    links = scraper._extract_links("<html><body></body></html>")
    assert links == []


# ---------------------------------------------------------------------------
# _get_next_url
# ---------------------------------------------------------------------------


def test_get_next_url_builds_correct_url(scraper):
    url = scraper._get_next_url(48, "notebook")
    assert "notebook" in url
    assert "_Desde_49_" in url


def test_get_next_url_empty_when_no_links(scraper):
    url = scraper._get_next_url(0, "notebook")
    assert url == ""


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@patch.object(MercadoLivreScraper, "retry_request")
def test_search_collects_links_across_pages(mock_retry, scraper):
    page1_html = _build_search_html(["https://ml.com/a", "https://ml.com/b"])
    page2_html = _build_search_html([])  # Empty → stop

    mock_retry.side_effect = [
        _mock_response(text=page1_html),
        _mock_response(text=page2_html),
    ]

    result = scraper.search("notebook", max_pages=5)
    assert "https://ml.com/a" in result
    assert "https://ml.com/b" in result
    assert len(result) == 2


@patch.object(MercadoLivreScraper, "retry_request")
def test_search_breaks_on_empty_html(mock_retry, scraper):
    mock_retry.return_value = _mock_response(text="")
    result = scraper.search("notebook", max_pages=5)
    assert result == []


@patch.object(MercadoLivreScraper, "retry_request")
def test_search_breaks_on_exception(mock_retry, scraper):
    mock_retry.side_effect = Exception("connection error")
    result = scraper.search("notebook", max_pages=3)
    assert result == []


# ---------------------------------------------------------------------------
# _extract_price / _extract_title / _extract_description
# ---------------------------------------------------------------------------


def test_extract_price_from_meta(scraper):
    soup = BeautifulSoup('<meta itemprop="price" content="1500.00"/>', "html.parser")
    assert scraper._extract_price(soup) == "1500.00"


def test_extract_price_returns_empty_when_missing(scraper):
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert scraper._extract_price(soup) == ""


def test_extract_title(scraper):
    soup = BeautifulSoup('<h1 class="ui-pdp-title">Notebook Dell</h1>', "html.parser")
    assert scraper._extract_title(soup) == "Notebook Dell"


def test_extract_title_returns_empty_when_missing(scraper):
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert scraper._extract_title(soup) == ""


def test_extract_description(scraper):
    soup = BeautifulSoup(
        '<p class="ui-pdp-description__content">Bom estado</p>', "html.parser"
    )
    assert scraper._extract_description(soup) == "Bom estado"


def test_extract_description_returns_empty_when_missing(scraper):
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert scraper._extract_description(soup) == ""


# ---------------------------------------------------------------------------
# _extract_availability
# ---------------------------------------------------------------------------


def test_extract_availability_true(scraper):
    soup = BeautifulSoup(
        '<p class="ui-pdp-stock-information__title">Disponível: 5 unidades</p>',
        "html.parser",
    )
    assert scraper._extract_availability(soup) is True


def test_extract_availability_false_when_not_available(scraper):
    soup = BeautifulSoup(
        '<p class="ui-pdp-stock-information__title">Sem estoque</p>', "html.parser"
    )
    assert scraper._extract_availability(soup) is False


def test_extract_availability_false_when_missing(scraper):
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert scraper._extract_availability(soup) is False


# ---------------------------------------------------------------------------
# _extract_product_code (static)
# ---------------------------------------------------------------------------


def test_extract_product_code_from_url_path():
    url = "https://www.mercadolivre.com.br/notebook-dell-inspiron-MLB123456789-_JM"
    code = MercadoLivreScraper._extract_product_code(url)
    assert code == "ML - MLB123456789"


def test_extract_product_code_fallback_to_wid_fragment():
    url = "https://www.mercadolivre.com.br/produto#wid=MLB999"
    code = MercadoLivreScraper._extract_product_code(url)
    assert code == "ML - MLB999"


def test_extract_product_code_fallback_to_path_segment():
    url = "https://www.mercadolivre.com.br/categoria/produto-nome"
    code = MercadoLivreScraper._extract_product_code(url)
    assert "ML - " in code
    assert "produto-nome" in code


# ---------------------------------------------------------------------------
# _extract_image_src
# ---------------------------------------------------------------------------


def test_extract_image_src_returns_src(scraper):
    soup = BeautifulSoup(
        '<img class="ui-pdp-image ui-pdp-gallery__figure__image" src="https://img.com/photo.jpg"/>',
        "html.parser",
    )
    assert scraper._extract_image_src(soup) == "https://img.com/photo.jpg"


def test_extract_image_src_returns_none_when_missing(scraper):
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert scraper._extract_image_src(soup) is None


# ---------------------------------------------------------------------------
# scrape_data
# ---------------------------------------------------------------------------


@patch.object(MercadoLivreScraper, "retry_request")
def test_scrape_data_returns_expected_fields(mock_retry, scraper):
    html_bytes = _build_product_html(
        title="Notebook Dell",
        price="3500.00",
        description="Muito bom",
        available=True,
        image_src="https://http2.mlstatic.com/img.jpg",
    )
    mock_retry.return_value = _mock_response(content=html_bytes)

    url = "https://www.mercadolivre.com.br/notebook-MLB123456789-_JM"
    result = scraper.scrape_data(url)

    assert result["url"] == url
    assert result["title"] == "Notebook Dell"
    assert result["price"] == "3500.00"
    assert result["description"] == "Muito bom"
    assert result["is_available"] is True
    assert result["image_urls"] == "https://http2.mlstatic.com/img.jpg"
    assert result["source_product_code"] == "ML - MLB123456789"
    assert result["city"] == "not found"
    assert result["state"] == "not found"


@patch.object(MercadoLivreScraper, "retry_request")
def test_scrape_data_unavailable_product(mock_retry, scraper):
    html_bytes = _build_product_html(available=False)
    mock_retry.return_value = _mock_response(content=html_bytes)

    result = scraper.scrape_data("https://www.mercadolivre.com.br/item-MLB1")
    assert result["is_available"] is False


# ---------------------------------------------------------------------------
# update_data
# ---------------------------------------------------------------------------


@patch.object(MercadoLivreScraper, "scrape_data")
def test_update_data_merges_fields(mock_scrape, scraper):
    mock_scrape.return_value = {
        "url": "https://ml.com/a",
        "title": "Updated Title",
        "price": "1200",
    }
    product = {"id": "55", "url": "https://ml.com/a", "title": "Old Title"}
    result = scraper.update_data(product)

    assert result["id"] == "55"
    assert result["title"] == "Updated Title"
    mock_scrape.assert_called_once_with("https://ml.com/a")
