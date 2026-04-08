"""
Tests for src/scrapers/estante_virtual.py.

Strategy: patch RotatingUserAgentMixin._load_user_agents so no real file I/O
happens, and mock Playwright async methods so no real browser is launched.
EstanteVirtual now uses PlaywrightScraper to bypass Radware Bot Manager.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from src.scrapers.estante_virtual import EstanteVirtualScraper

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _build_search_json(total_pages: int, skus: list[dict]) -> dict:
    """Minimal API response from EstanteVirtual /busca/api."""
    return {"totalPages": total_pages, "parentSkus": skus}


def _make_async_page(body_text: str = "", html_content: str = ""):
    """Create an async mock (context, page) pair.

    *body_text* — returned by ``page.locator("body").text_content()``
    *html_content* — returned by ``page.content()``
    """
    context = AsyncMock()
    page = AsyncMock()

    resp = AsyncMock()
    resp.status = 200
    page.goto = AsyncMock(return_value=resp)

    locator = AsyncMock()
    locator.text_content = AsyncMock(return_value=body_text)
    page.locator = MagicMock(return_value=locator)

    page.content = AsyncMock(return_value=html_content)

    return context, page


def _build_product_html(
    title: str = "Dom Casmurro",
    author: str = "Machado de Assis",
    sale_in_cents: int = 2500,
    description: str = "Ótimo estado",
    seller_name: str = "Livraria ABC",
    available: bool = True,
    image_slug: str = "/images/book.jpg",
    product_id: int = 42,
    city: str = "São Paulo",
) -> str:
    """Build an HTML page with window.__INITIAL_STATE__ JSON embedded."""
    state = {
        "Product": {
            # name and author are at the Product level (used by scrape_data)
            "name": title,
            "author": author,
            "id": product_id,
            "currentProduct": {
                "id": product_id,
                "description": description,
                "available": available,
                "sku": f"EV{product_id}",
                "price": {
                    "saleInCents": sale_in_cents,
                    "seller": {"name": seller_name},
                },
                "images": {"details": [image_slug]},
            },
            "grouper": {
                "groupProducts": {
                    "novo": {
                        "salePrice": sale_in_cents,
                        "prices": [{"city": city}],
                    }
                }
            },
        }
    }
    json_str = json.dumps(state)
    return f"""<html><body>
        <script>window.__INITIAL_STATE__ = {json_str};</script>
    </body></html>"""


@pytest.fixture
def scraper():
    with patch.object(EstanteVirtualScraper, "_load_user_agents", return_value=[]):
        s = EstanteVirtualScraper()
    return s


# ---------------------------------------------------------------------------
# __init__ / BASE_URL
# ---------------------------------------------------------------------------


def test_base_url(scraper):
    assert scraper.BASE_URL == "https://www.estantevirtual.com.br"


def test_str(scraper):
    assert str(scraper) == "Estante Virtual Scraper"


# ---------------------------------------------------------------------------
# _build_default_headers
# ---------------------------------------------------------------------------


def test_build_default_headers_keys(scraper):
    headers = EstanteVirtualScraper._build_default_headers()
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
    scraper._user_agents = ["Mozilla/5.0 EV-Test"]
    result = scraper.headers()
    assert result["User-Agent"] == "Mozilla/5.0 EV-Test"


# ---------------------------------------------------------------------------
# _get_products_list
# ---------------------------------------------------------------------------


def test_get_products_list_builds_urls(scraper):
    data = {
        "parentSkus": [
            {"productSlug": "/livros/dom-casmurro-1"},
            {"productSlug": "/livros/quincas-2"},
        ]
    }
    result = scraper._get_products_list(data)
    assert result == [
        "https://www.estantevirtual.com.br/livros/dom-casmurro-1",
        "https://www.estantevirtual.com.br/livros/quincas-2",
    ]


def test_get_products_list_empty(scraper):
    data = {"parentSkus": []}
    assert scraper._get_products_list(data) == []


# ---------------------------------------------------------------------------
# search (async, mocked Playwright)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_single_page(scraper):
    skus = [{"productSlug": "/livros/a"}, {"productSlug": "/livros/b"}]
    search_json = _build_search_json(total_pages=1, skus=skus)
    body_text = json.dumps(search_json)

    context, page = _make_async_page(body_text=body_text)

    with patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))):
        result = await scraper._search_async("Dom Casmurro")

    assert len(result) == 2
    assert "https://www.estantevirtual.com.br/livros/a" in result
    context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_multiple_pages(scraper):
    """When page_number < totalPages, continues; when equal, stops."""
    skus_p1 = [{"productSlug": "/livros/p1"}]
    skus_p2 = [{"productSlug": "/livros/p2"}]

    body_p1 = json.dumps(_build_search_json(2, skus_p1))
    body_p2 = json.dumps(_build_search_json(2, skus_p2))

    context, page = _make_async_page()
    locator = AsyncMock()
    locator.text_content = AsyncMock(side_effect=[body_p1, body_p2])
    page.locator = MagicMock(return_value=locator)

    with (
        patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))),
        patch("src.scrapers.estante_virtual.asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await scraper._search_async("Machado")

    assert len(result) == 2
    assert page.goto.await_count == 2


@pytest.mark.asyncio
async def test_search_stops_on_failed_goto(scraper):
    """When page.goto raises, search stops and returns empty."""
    context, page = _make_async_page()
    page.goto = AsyncMock(side_effect=Exception("Timeout"))

    with patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))):
        result = await scraper._search_async("whatever")

    assert result == []
    context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_stops_on_non_200(scraper):
    """When response status is not 200, search stops."""
    context, page = _make_async_page()
    resp = AsyncMock()
    resp.status = 403
    page.goto = AsyncMock(return_value=resp)

    with patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))):
        result = await scraper._search_async("blocked")

    assert result == []


@pytest.mark.asyncio
async def test_search_stops_on_empty_body(scraper):
    """When body text is empty, search stops."""
    context, page = _make_async_page(body_text="")
    locator = AsyncMock()
    locator.text_content = AsyncMock(return_value="")
    page.locator = MagicMock(return_value=locator)

    with patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))):
        result = await scraper._search_async("empty")

    assert result == []


@pytest.mark.asyncio
async def test_search_stops_on_non_json_body(scraper):
    """When body is HTML (anti-bot captcha), search stops gracefully."""
    context, page = _make_async_page(body_text="<html>captcha page</html>")

    with patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))):
        result = await scraper._search_async("Dom Casmurro")

    assert result == []


@pytest.mark.asyncio
async def test_search_returns_partial_on_antibot_midway(scraper):
    """If anti-bot kicks in on page 2, page 1 results are still returned."""
    skus_p1 = [{"productSlug": "/livros/p1"}]
    body_p1 = json.dumps(_build_search_json(3, skus_p1))

    context, page = _make_async_page()
    locator = AsyncMock()
    locator.text_content = AsyncMock(side_effect=[body_p1, "<html>blocked</html>"])
    page.locator = MagicMock(return_value=locator)

    with (
        patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))),
        patch("src.scrapers.estante_virtual.asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await scraper._search_async("Machado")

    assert len(result) == 1
    assert "https://www.estantevirtual.com.br/livros/p1" in result


@pytest.mark.asyncio
async def test_search_stops_on_none_response(scraper):
    """When page.goto returns None, search stops."""
    context, page = _make_async_page()
    page.goto = AsyncMock(return_value=None)

    with patch.object(scraper, "new_page", AsyncMock(return_value=(context, page))):
        result = await scraper._search_async("whatever")

    assert result == []


# ---------------------------------------------------------------------------
# _parse_html
# ---------------------------------------------------------------------------


def test_parse_html_returns_beautifulsoup(scraper):
    result = scraper._parse_html(b"<html><body>ok</body></html>")
    assert isinstance(result, BeautifulSoup)


# ---------------------------------------------------------------------------
# _extract_initial_state
# ---------------------------------------------------------------------------


def test_extract_initial_state_returns_dict(scraper):
    html_str = _build_product_html()
    soup = scraper._parse_html(html_str.encode())
    state = scraper._extract_initial_state(soup)
    assert "Product" in state


def test_extract_initial_state_returns_empty_when_no_script(scraper):
    soup = scraper._parse_html(b"<html><body></body></html>")
    assert scraper._extract_initial_state(soup) == {}


# ---------------------------------------------------------------------------
# _extract_product_info
# ---------------------------------------------------------------------------


def test_extract_product_info(scraper):
    data = {"Product": {"currentProduct": {"name": "Book"}}}
    result = scraper._extract_product_info(data)
    assert result == {"currentProduct": {"name": "Book"}}


# ---------------------------------------------------------------------------
# _extract_price
# ---------------------------------------------------------------------------


def test_extract_price_converts_cents(scraper):
    product_info = {"currentProduct": {"price": {"saleInCents": 3000}}}
    assert scraper._extract_price(product_info) == pytest.approx(30.0)


def test_extract_price_raises_when_missing(scraper):
    product_info = {"currentProduct": {"price": {}}}
    with pytest.raises(ValueError, match="Price not found"):
        scraper._extract_price(product_info)


# ---------------------------------------------------------------------------
# _extract_description
# ---------------------------------------------------------------------------


def test_extract_description(scraper):
    product_info = {"currentProduct": {"description": "Excelente livro"}}
    assert scraper._extract_description(product_info) == "Excelente livro"


def test_extract_description_returns_empty_when_missing(scraper):
    assert scraper._extract_description({}) == ""


# ---------------------------------------------------------------------------
# _extract_seller
# ---------------------------------------------------------------------------


def test_extract_seller(scraper):
    product_info = {"currentProduct": {"price": {"seller": {"name": "Livraria XYZ"}}}}
    assert scraper._extract_seller(product_info) == "Livraria XYZ"


# ---------------------------------------------------------------------------
# _extract_location
# ---------------------------------------------------------------------------


def test_extract_location_from_novo(scraper):
    product_info = {
        "grouper": {"groupProducts": {"novo": {"prices": [{"city": "Campinas"}]}}}
    }
    assert scraper._extract_location(product_info) == "Campinas"


def test_extract_location_from_usado_when_no_novo(scraper):
    product_info = {
        "grouper": {"groupProducts": {"usado": {"prices": [{"city": "Recife"}]}}}
    }
    assert scraper._extract_location(product_info) == "Recife"


def test_extract_location_returns_empty_when_no_grouper(scraper):
    assert scraper._extract_location({}) == ""


def test_extract_location_returns_empty_when_prices_empty(scraper):
    product_info = {"grouper": {"groupProducts": {"novo": {"prices": []}}}}
    assert scraper._extract_location(product_info) == ""


# ---------------------------------------------------------------------------
# _extract_image
# ---------------------------------------------------------------------------


def test_extract_image_returns_full_url(scraper):
    product_info = {"currentProduct": {"images": {"details": ["/img/book.jpg"]}}}
    url = scraper._extract_image(product_info)
    assert url == "https://static.estantevirtual.com.br/img/book.jpg"


def test_extract_image_returns_empty_when_no_details(scraper):
    product_info = {"currentProduct": {"images": {"details": []}}}
    assert scraper._extract_image(product_info) == ""


def test_extract_image_returns_empty_when_missing(scraper):
    assert scraper._extract_image({}) == ""


# ---------------------------------------------------------------------------
# _extract_is_available
# ---------------------------------------------------------------------------


def test_extract_is_available_true(scraper):
    product_info = {"currentProduct": {"available": True}}
    assert scraper._extract_is_available(product_info) is True


def test_extract_is_available_false(scraper):
    product_info = {"currentProduct": {"available": False}}
    assert scraper._extract_is_available(product_info) is False


# ---------------------------------------------------------------------------
# _extract_prices (plural, used for condition grouping)
# ---------------------------------------------------------------------------


def test_extract_prices_combines_novo_usado(scraper):
    product_info = {
        "grouper": {
            "groupProducts": {
                "novo": {"salePrice": 5000},
                "usado": {"salePrice": 3000},
            }
        }
    }
    prices = scraper._extract_prices(product_info)
    assert len(prices) == 2
    assert pytest.approx(50.0) in prices
    assert pytest.approx(30.0) in prices


def test_extract_prices_empty_when_no_grouper(scraper):
    assert scraper._extract_prices({}) == []


# ---------------------------------------------------------------------------
# scrape_data (async, mocked Playwright)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_data_returns_expected_fields(scraper):
    html = _build_product_html(
        title="Dom Casmurro",
        author="Machado de Assis",
        sale_in_cents=2500,
        description="Clássico brasileiro",
        seller_name="Livraria São Paulo",
        available=True,
        image_slug="/images/dom.jpg",
        product_id=99,
        city="Rio de Janeiro",
    )
    context, page = _make_async_page(html_content=html)

    with patch.object(scraper, "fetch_page", AsyncMock(return_value=(context, page))):
        result = await scraper._scrape_data_async(
            "https://www.estantevirtual.com.br/livros/dom-casmurro"
        )

    assert result["url"] == "https://www.estantevirtual.com.br/livros/dom-casmurro"
    assert "Dom Casmurro" in result["title"]
    assert "Machado de Assis" in result["title"]
    assert result["price"] == "25.00"
    assert result["description"] == "Clássico brasileiro"
    assert result["seller_name"] == "Livraria São Paulo"
    assert result["city"] == "Rio de Janeiro"
    assert result["is_available"] is True
    assert result["image_urls"] == "https://static.estantevirtual.com.br/images/dom.jpg"
    assert result["source_product_code"] == "EV - 99"
    context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_scrape_data_returns_empty_when_no_initial_state(scraper):
    context, page = _make_async_page(
        html_content="<html><body>no state here</body></html>"
    )

    with patch.object(scraper, "fetch_page", AsyncMock(return_value=(context, page))):
        result = await scraper._scrape_data_async(
            "https://www.estantevirtual.com.br/livros/unknown"
        )

    assert result == {}
    context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_scrape_data_raises_on_fetch_error(scraper):
    with (
        patch.object(
            scraper, "fetch_page", AsyncMock(side_effect=Exception("Network error"))
        ),
        pytest.raises(Exception, match="Network error"),
    ):
        await scraper._scrape_data_async("https://www.estantevirtual.com.br/x")


# ---------------------------------------------------------------------------
# update_data
# ---------------------------------------------------------------------------


@patch.object(EstanteVirtualScraper, "scrape_data")
def test_update_data_merges_product_data(mock_scrape, scraper):
    mock_scrape.return_value = {
        "url": "https://www.estantevirtual.com.br/livros/a",
        "title": "Updated Title",
        "price": "15.00",
    }
    product = {
        "id": "77",
        "url": "https://www.estantevirtual.com.br/livros/a",
        "title": "Old Title",
    }
    result = scraper.update_data(product)

    assert result["id"] == "77"
    assert result["title"] == "Updated Title"
    mock_scrape.assert_called_once_with(product["url"])
