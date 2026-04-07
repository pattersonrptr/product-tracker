"""
Tests for src/scrapers/mercado_livre.py (Playwright-based version).

Strategy: mock Playwright Page/Context objects so no real browser is launched.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from src.scrapers.mercado_livre import MercadoLivreScraper

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _mock_element(text: str = "", attribute: str | None = None):
    """Create a mock Playwright ElementHandle."""
    el = MagicMock()
    el.inner_text.return_value = text
    el.get_attribute.return_value = attribute
    return el


def _mock_page(
    title: str = "Notebook Dell",
    price_meta: str = "3500.00",
    description: str = "Descrição do produto",
    stock_text: str | None = "Disponível: 10 unidades",
    image_src: str | None = "https://http2.mlstatic.com/img.jpg",
    seller: str | None = "Loja Oficial",
    location: str | None = "São Paulo",
    search_links: list[str] | None = None,
    has_next_page: bool = False,
):
    """Create a mock Playwright Page with configurable query_selector results."""
    page = MagicMock()

    def query_selector(selector):
        if selector == "h1.ui-pdp-title":
            return _mock_element(text=title) if title else None
        if selector == 'meta[itemprop="price"]':
            if price_meta:
                return _mock_element(attribute=price_meta)
            return None
        if selector == ".andes-money-amount__fraction":
            return None
        if selector == "p.ui-pdp-description__content":
            return _mock_element(text=description) if description else None
        if selector == ".ui-pdp-stock-information__title":
            if stock_text:
                return _mock_element(text=stock_text)
            return None
        if selector == "img.ui-pdp-image.ui-pdp-gallery__figure__image":
            if image_src:
                return _mock_element(attribute=image_src)
            return None
        if selector == "figure.ui-pdp-gallery__figure img":
            return None
        if selector == ".ui-pdp-seller__link-trigger-button":
            if seller:
                return _mock_element(text=seller)
            return None
        if selector == ".ui-pdp-seller__header__title":
            return None
        if selector == ".ui-pdp-media__body p":
            if location:
                return _mock_element(text=location)
            return None
        if selector == "a.andes-pagination__link[title='Seguinte']":
            return MagicMock() if has_next_page else None
        return None

    page.query_selector = MagicMock(side_effect=query_selector)
    page.goto = MagicMock()
    page.wait_for_selector = MagicMock()

    # For _extract_links
    if search_links is not None:
        page.eval_on_selector_all = MagicMock(return_value=search_links)
    else:
        page.eval_on_selector_all = MagicMock(return_value=[])

    return page


def _mock_context():
    ctx = MagicMock()
    ctx.close = MagicMock()
    return ctx


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


def test_build_default_headers_keys():
    headers = MercadoLivreScraper._build_default_headers()
    assert "Accept" in headers
    assert "Accept-Language" in headers


# ---------------------------------------------------------------------------
# headers()
# ---------------------------------------------------------------------------


def test_headers_always_uses_chrome_ua(scraper):
    result = scraper.headers()
    assert "Accept" in result
    assert "User-Agent" in result
    assert "Chrome" in result["User-Agent"]


def test_headers_uses_class_chrome_ua(scraper):
    result = scraper.headers()
    assert result["User-Agent"] == MercadoLivreScraper._CHROME_UA


# ---------------------------------------------------------------------------
# _build_search_url
# ---------------------------------------------------------------------------


def test_build_search_url_first_page(scraper):
    url = scraper._build_search_url("notebook", offset=0)
    assert url == "https://lista.mercadolivre.com.br/notebook"


def test_build_search_url_subsequent_page(scraper):
    url = scraper._build_search_url("notebook", offset=48)
    assert "notebook" in url
    assert "_Desde_49_" in url
    assert "_NoIndex_True" in url


# ---------------------------------------------------------------------------
# _extract_links
# ---------------------------------------------------------------------------


def test_extract_links_returns_product_links(scraper):
    page = _mock_page(
        search_links=["https://ml.com/a", "https://ml.com/b"]
    )
    links = scraper._extract_links(page)
    assert "https://ml.com/a" in links
    assert "https://ml.com/b" in links


def test_extract_links_filters_click1_tracker(scraper):
    page = _mock_page(
        search_links=[
            "https://ml.com/a",
            "https://click1.mercadolivre.com.br/tracker",
        ]
    )
    links = scraper._extract_links(page)
    assert "https://ml.com/a" in links
    assert not any("click1" in link for link in links)


def test_extract_links_empty_when_no_items(scraper):
    page = _mock_page(search_links=[])
    links = scraper._extract_links(page)
    assert links == []


def test_extract_links_deduplicates(scraper):
    page = _mock_page(
        search_links=["https://ml.com/a", "https://ml.com/a", "https://ml.com/b"]
    )
    links = scraper._extract_links(page)
    assert links == ["https://ml.com/a", "https://ml.com/b"]


def test_extract_links_skips_empty_href(scraper):
    page = _mock_page(search_links=["", None, "https://ml.com/a"])
    links = scraper._extract_links(page)
    assert links == ["https://ml.com/a"]


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@patch("src.scrapers.mercado_livre.time.sleep")
def test_search_collects_links_across_pages(mock_sleep, scraper):
    page1 = _mock_page(
        search_links=["https://ml.com/a", "https://ml.com/b"],
        has_next_page=True,
    )
    page2 = _mock_page(
        search_links=["https://ml.com/c"],
        has_next_page=False,
    )

    ctx = _mock_context()
    pages = iter([page1, page2])

    with patch.object(scraper, "start"):
        with patch.object(scraper, "new_page", side_effect=lambda: (ctx, next(pages))):
            # new_page is called once in search (before the loop), but
            # the scraper reuses the same page — so we patch it once
            # Actually search() calls new_page() once and reuses the page.
            # Let's align with the actual implementation.
            pass

    # The implementation calls new_page() once and reuses the same page.
    # So we need a single page that simulates two rounds of interaction.
    page = MagicMock()
    ctx = _mock_context()

    call_count = 0

    def fake_extract_links(p):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ["https://ml.com/a", "https://ml.com/b"]
        return []

    next_btn_count = 0

    def fake_query_selector(selector):
        nonlocal next_btn_count
        if selector == "a.andes-pagination__link[title='Seguinte']":
            next_btn_count += 1
            if next_btn_count == 1:
                return MagicMock()
            return None
        return None

    page.goto = MagicMock()
    page.wait_for_selector = MagicMock()
    page.query_selector = MagicMock(side_effect=fake_query_selector)

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
        patch.object(scraper, "_extract_links", side_effect=fake_extract_links),
    ):
        result = scraper.search("notebook", max_pages=5)

    assert "https://ml.com/a" in result
    assert "https://ml.com/b" in result
    assert len(result) == 2
    ctx.close.assert_called_once()


@patch("src.scrapers.mercado_livre.time.sleep")
def test_search_stops_on_empty_links(mock_sleep, scraper):
    page = MagicMock()
    page.goto = MagicMock()
    page.wait_for_selector = MagicMock()
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
        patch.object(scraper, "_extract_links", return_value=[]),
    ):
        with pytest.raises(Exception, match="No results found"):
            scraper.search("notebook", max_pages=5)

    ctx.close.assert_called_once()


@patch("src.scrapers.mercado_livre.time.sleep")
def test_search_stops_on_page_load_error(mock_sleep, scraper):
    page = MagicMock()
    page.goto.side_effect = Exception("Timeout")
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
    ):
        with pytest.raises(Exception, match="No results found"):
            scraper.search("notebook", max_pages=3)

    ctx.close.assert_called_once()


@patch("src.scrapers.mercado_livre.time.sleep")
def test_search_stops_when_no_next_button(mock_sleep, scraper):
    page = MagicMock()
    page.goto = MagicMock()
    page.wait_for_selector = MagicMock()
    page.query_selector = MagicMock(return_value=None)  # No next button
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
        patch.object(
            scraper, "_extract_links", return_value=["https://ml.com/a"]
        ),
    ):
        result = scraper.search("notebook", max_pages=5)

    assert result == ["https://ml.com/a"]


@patch("src.scrapers.mercado_livre.time.sleep")
def test_search_context_closed_on_error(mock_sleep, scraper):
    """Ensure the context is closed even when an unexpected error occurs."""
    page = MagicMock()
    page.goto = MagicMock()
    page.wait_for_selector = MagicMock()
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
        patch.object(
            scraper, "_extract_links", side_effect=RuntimeError("boom")
        ),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            scraper.search("notebook", max_pages=1)

    ctx.close.assert_called_once()


# ---------------------------------------------------------------------------
# _extract_price
# ---------------------------------------------------------------------------


def test_extract_price_from_meta(scraper):
    page = _mock_page(price_meta="1500.00")
    assert scraper._extract_price(page) == "1500.00"


def test_extract_price_fallback_to_fraction(scraper):
    page = MagicMock()

    def qs(selector):
        if selector == 'meta[itemprop="price"]':
            return None
        if selector == ".andes-money-amount__fraction":
            return _mock_element(text="2499")
        return None

    page.query_selector = MagicMock(side_effect=qs)
    assert scraper._extract_price(page) == "2499"


def test_extract_price_returns_empty_when_missing(scraper):
    page = _mock_page(price_meta=None)
    # Both meta and fraction return None
    assert scraper._extract_price(page) == ""


# ---------------------------------------------------------------------------
# _extract_title
# ---------------------------------------------------------------------------


def test_extract_title(scraper):
    page = _mock_page(title="Notebook Dell")
    assert scraper._extract_title(page) == "Notebook Dell"


def test_extract_title_returns_empty_when_missing(scraper):
    page = _mock_page(title=None)
    assert scraper._extract_title(page) == ""


# ---------------------------------------------------------------------------
# _extract_description
# ---------------------------------------------------------------------------


def test_extract_description(scraper):
    page = _mock_page(description="Bom estado")
    assert scraper._extract_description(page) == "Bom estado"


def test_extract_description_returns_empty_when_missing(scraper):
    page = _mock_page(description=None)
    assert scraper._extract_description(page) == ""


# ---------------------------------------------------------------------------
# _extract_availability
# ---------------------------------------------------------------------------


def test_extract_availability_true_from_stock_info(scraper):
    page = _mock_page(stock_text="Disponível: 5 unidades", price_meta="100")
    assert scraper._extract_availability(page) is True


def test_extract_availability_true_from_price_fallback(scraper):
    page = _mock_page(stock_text=None, price_meta="100")
    assert scraper._extract_availability(page) is True


def test_extract_availability_false_when_out_of_stock(scraper):
    page = _mock_page(stock_text="Sem estoque", price_meta=None)
    assert scraper._extract_availability(page) is False


def test_extract_availability_false_when_nothing(scraper):
    page = _mock_page(stock_text=None, price_meta=None)
    assert scraper._extract_availability(page) is False


# ---------------------------------------------------------------------------
# _extract_product_code (static — unchanged)
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
    page = _mock_page(image_src="https://img.com/photo.jpg")
    assert scraper._extract_image_src(page) == "https://img.com/photo.jpg"


def test_extract_image_src_fallback_to_figure(scraper):
    page = MagicMock()

    def qs(selector):
        if selector == "img.ui-pdp-image.ui-pdp-gallery__figure__image":
            return None
        if selector == "figure.ui-pdp-gallery__figure img":
            return _mock_element(attribute="https://fallback.jpg")
        return None

    page.query_selector = MagicMock(side_effect=qs)
    assert scraper._extract_image_src(page) == "https://fallback.jpg"


def test_extract_image_src_returns_none_when_missing(scraper):
    page = _mock_page(image_src=None)
    assert scraper._extract_image_src(page) is None


# ---------------------------------------------------------------------------
# _extract_seller
# ---------------------------------------------------------------------------


def test_extract_seller(scraper):
    page = _mock_page(seller="Loja Oficial")
    assert scraper._extract_seller(page) == "Loja Oficial"


def test_extract_seller_fallback_to_header_title(scraper):
    page = MagicMock()

    def qs(selector):
        if selector == ".ui-pdp-seller__link-trigger-button":
            return None
        if selector == ".ui-pdp-seller__header__title":
            return _mock_element(text="Vendedor Teste")
        return None

    page.query_selector = MagicMock(side_effect=qs)
    assert scraper._extract_seller(page) == "Vendedor Teste"


def test_extract_seller_not_found(scraper):
    page = _mock_page(seller=None)
    assert scraper._extract_seller(page) == "not found"


# ---------------------------------------------------------------------------
# _extract_location
# ---------------------------------------------------------------------------


def test_extract_location(scraper):
    page = _mock_page(location="São Paulo")
    assert scraper._extract_location(page) == "São Paulo"


def test_extract_location_not_found(scraper):
    page = _mock_page(location=None)
    assert scraper._extract_location(page) == "not found"


# ---------------------------------------------------------------------------
# scrape_data
# ---------------------------------------------------------------------------


def test_scrape_data_returns_expected_fields(scraper):
    page = _mock_page(
        title="Notebook Dell",
        price_meta="3500.00",
        description="Muito bom",
        stock_text="Disponível: 10 unidades",
        image_src="https://http2.mlstatic.com/img.jpg",
        seller="Loja Dell",
        location="Curitiba - PR",
    )
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
    ):
        url = "https://www.mercadolivre.com.br/notebook-MLB123456789-_JM"
        result = scraper.scrape_data(url)

    assert result["url"] == url
    assert result["title"] == "Notebook Dell"
    assert result["price"] == "3500.00"
    assert result["description"] == "Muito bom"
    assert result["is_available"] is True
    assert result["image_urls"] == "https://http2.mlstatic.com/img.jpg"
    assert result["source_product_code"] == "ML - MLB123456789"
    assert result["city"] == "Curitiba - PR"
    assert result["state"] == "not found"
    assert result["seller_name"] == "Loja Dell"
    ctx.close.assert_called_once()


def test_scrape_data_unavailable_product(scraper):
    page = _mock_page(stock_text=None, price_meta=None)
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
    ):
        result = scraper.scrape_data("https://www.mercadolivre.com.br/item-MLB1")

    assert result["is_available"] is False
    ctx.close.assert_called_once()


def test_scrape_data_closes_context_on_error(scraper):
    page = MagicMock()
    page.goto.side_effect = RuntimeError("Timeout")
    ctx = _mock_context()

    with (
        patch.object(scraper, "start"),
        patch.object(scraper, "stop"),
        patch.object(scraper, "new_page", return_value=(ctx, page)),
        pytest.raises(RuntimeError, match="Timeout"),
    ):
        scraper.scrape_data("https://www.mercadolivre.com.br/item-MLB1")

    ctx.close.assert_called_once()


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
