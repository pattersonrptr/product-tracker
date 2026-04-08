"""
Tests for src/scrapers/olx.py (Playwright async-based version).

Strategy: mock Playwright async API so no real browser is launched.
"""

import html
import json
from unittest.mock import AsyncMock, patch

import pytest

from src.scrapers.olx import OLXScraper

# ---------------------------------------------------------------------------
# Helpers / fixtures
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
) -> str:
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
    data_json = html.escape(json.dumps({"ad": ad}))
    return f'<html><body><script id="initial-data" data-json="{data_json}"></script></body></html>'


def _make_mock_page(html_content: str):
    """Create a mock Playwright page that returns given html_content."""
    page = AsyncMock()
    page.content = AsyncMock(return_value=html_content)
    page.goto = AsyncMock()
    context = AsyncMock()
    context.close = AsyncMock()
    return context, page


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
# search (async via _search_async directly)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_single_page(scraper):
    ads = [{"url": "https://olx.com/a"}, {"url": "https://olx.com/b"}]
    html_content = _build_olx_html(ads)

    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(side_effect=[html_content, "<html></html>"])
    page.goto = AsyncMock()

    async def fake_fetch(url, wait_until="networkidle"):
        return ctx, page

    with (
        patch.object(scraper, "fetch_page", side_effect=fake_fetch),
        patch("src.scrapers.olx.asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await scraper._search_async("notebook", max_pages=5)

    assert "https://olx.com/a" in result
    assert "https://olx.com/b" in result


@pytest.mark.asyncio
async def test_search_empty_html_breaks_loop_raises_no_results(scraper):
    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(return_value="")
    page.goto = AsyncMock()

    with (
        patch.object(scraper, "fetch_page", return_value=(ctx, page)),
        pytest.raises(Exception, match="No results found"),
    ):
        await scraper._search_async("notebook", max_pages=5)


@pytest.mark.asyncio
async def test_search_raises_when_first_page_returns_none(scraper):
    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(return_value=None)
    page.goto = AsyncMock()

    with (
        patch.object(scraper, "fetch_page", return_value=(ctx, page)),
        pytest.raises(Exception, match="No results found"),
    ):
        await scraper._search_async("notebook", max_pages=5)


@pytest.mark.asyncio
async def test_search_raises_when_no_results(scraper):
    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(return_value="<html><body></body></html>")
    page.goto = AsyncMock()

    with (
        patch.object(scraper, "fetch_page", return_value=(ctx, page)),
        pytest.raises(Exception, match="No results found"),
    ):
        await scraper._search_async("nothing", max_pages=1)


# ---------------------------------------------------------------------------
# _extract_json_data
# ---------------------------------------------------------------------------


def test_extract_json_data_returns_ad(scraper):
    html_str = _build_product_html(subject="Book", list_id="42", price_value="R$30,00")
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_str, "html.parser")
    data = scraper._extract_json_data(soup)
    assert data["subject"] == "Book"
    assert data["listId"] == "42"


def test_extract_json_data_returns_empty_when_no_script(scraper):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup("<html></html>", "html.parser")
    data = scraper._extract_json_data(soup)
    assert data == {}


# ---------------------------------------------------------------------------
# scrape_data (async via _run_async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_data_returns_expected_fields(scraper):
    html_str = _build_product_html(
        subject="Old Bike",
        list_id="777",
        price_value="R$1.200,00",
        body="Ótimo estado",
        seller_name="Maria",
        city="Curitiba",
        uf="PR",
    )
    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(return_value=html_str)
    page.goto = AsyncMock()

    with patch.object(scraper, "fetch_page", return_value=(ctx, page)):
        result = await scraper._scrape_data_async("https://olx.com/item/777")

    assert result["url"] == "https://olx.com/item/777"
    assert result["title"] == "Old Bike"
    assert result["description"] == "Ótimo estado"
    assert result["seller_name"] == "Maria"
    assert result["city"] == "Curitiba"
    assert result["state"] == "PR"
    assert result["source_product_code"] == "OLX - 777"
    assert result["image_urls"] == "https://img.olx.com.br/1.jpg"
    assert result["is_available"] is True


@pytest.mark.asyncio
async def test_scrape_data_no_price_is_unavailable(scraper):
    html_str = _build_product_html(price_value="")
    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(return_value=html_str)
    page.goto = AsyncMock()

    with patch.object(scraper, "fetch_page", return_value=(ctx, page)):
        result = await scraper._scrape_data_async("https://olx.com/item/123")
    assert result["is_available"] is False


@pytest.mark.asyncio
async def test_scrape_data_no_images(scraper):
    html_str = _build_product_html(images=[])
    ctx = AsyncMock()
    ctx.close = AsyncMock()
    page = AsyncMock()
    page.content = AsyncMock(return_value=html_str)
    page.goto = AsyncMock()

    with patch.object(scraper, "fetch_page", return_value=(ctx, page)):
        result = await scraper._scrape_data_async("https://olx.com/item/123")
    assert result["image_urls"] == ""


# ---------------------------------------------------------------------------
# update_data
# ---------------------------------------------------------------------------


@patch.object(OLXScraper, "scrape_data")
@pytest.mark.asyncio
async def test_update_data_merges_and_preserves_id(mock_scrape, scraper):
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
@pytest.mark.asyncio
async def test_update_data_without_id(mock_scrape, scraper):
    """If product has no 'id', update_data still works."""
    mock_scrape.return_value = {"url": "https://olx.com/a", "title": "New"}
    product = {"url": "https://olx.com/a"}
    result = scraper.update_data(product)
    assert "id" not in result
    assert result["title"] == "New"
