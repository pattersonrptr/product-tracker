from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scrapers.enjoei import EnjoeiScraper

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scraper():
    with patch.object(EnjoeiScraper, "_load_user_agents", return_value=[]):
        return EnjoeiScraper()


# ---------------------------------------------------------------------------
# __str__
# ---------------------------------------------------------------------------


def test_str_representation(scraper):
    assert str(scraper) == "Enjoei Scraper"


# ---------------------------------------------------------------------------
# headers
# ---------------------------------------------------------------------------


def test_headers_uses_random_user_agent_when_available(scraper):
    with patch.object(scraper, "get_random_user_agent", return_value="CustomAgent/1.0"):
        headers = scraper.headers()
    assert headers["User-Agent"] == "CustomAgent/1.0"
    assert "Accept-Language" in headers


def test_headers_falls_back_to_default_when_no_random_agent(scraper):
    with patch.object(scraper, "get_random_user_agent", return_value=None):
        headers = scraper.headers()
    assert headers["User-Agent"].startswith("Mozilla/")
    assert "Accept-Language" in headers
    assert "DNT" in headers


def test_build_default_headers_contains_expected_keys():
    h = EnjoeiScraper._build_default_headers()
    assert "User-Agent" in h
    assert "Accept-Language" in h
    assert "DNT" in h
    assert "Sec-GPC" in h


# ---------------------------------------------------------------------------
# _get_search_data
# ---------------------------------------------------------------------------


def _make_enjoei_page_response(json_data):
    """Create a mock (context, page) pair for fetch_page_sync."""
    import json as json_mod

    ctx = MagicMock()
    ctx.close = MagicMock()

    # For _get_search_data: page.locator("body").text_content() — sync call
    text_content_val = json_mod.dumps(json_data)
    locator_result = MagicMock()
    locator_result.text_content = MagicMock(return_value=text_content_val)
    page = MagicMock()
    page.locator = MagicMock(return_value=locator_result)
    page.goto = MagicMock()
    return ctx, page


def _make_scrape_page_response(data):
    import json as json_mod
    ctx = MagicMock()
    ctx.close = MagicMock()

    text_content_val = json_mod.dumps(data)
    locator_result = MagicMock()
    locator_result.text_content = MagicMock(return_value=text_content_val)
    page = MagicMock()
    page.locator = MagicMock(return_value=locator_result)
    page.goto = MagicMock()
    return ctx, page


def test_get_search_data_calls_fetch_page_with_correct_params(scraper):
    mock_data = {"data": {"search": {"products": {"edges": []}}}}
    ctx, page = _make_enjoei_page_response(mock_data)

    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)) as mock_fetch:
        scraper._get_search_data("notebook")

    mock_fetch.assert_called_once()
    call_args = mock_fetch.call_args
    assert "graphql-search-x" in call_args[0][0]
    assert "term=notebook" in call_args[0][0]


def test_get_search_data_passes_after_cursor_when_provided(scraper):
    mock_data = {"data": {"search": {"products": {"edges": []}}}}
    ctx, page = _make_enjoei_page_response(mock_data)

    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)) as mock_fetch:
        scraper._get_search_data("fone", after="CURSOR_ABC")

    call_args = mock_fetch.call_args
    assert "after=CURSOR_ABC" in call_args[0][0]


def test_get_search_data_omits_after_when_none(scraper):
    mock_data = {"data": {"search": {"products": {"edges": []}}}}
    ctx, page = _make_enjoei_page_response(mock_data)

    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)) as mock_fetch:
        scraper._get_search_data("fone", after=None)

    call_args = mock_fetch.call_args
    assert "after" not in call_args[0][0]


# ---------------------------------------------------------------------------
# _extract_links
# ---------------------------------------------------------------------------


def _make_edges(*ids_and_cursors):
    """Helper: build an Enjoei-style edges list."""
    edges = []
    for id_, cursor in ids_and_cursors:
        edge = {"node": {"id": id_}, "cursor": cursor}
        edges.append(edge)
    return {"data": {"search": {"products": {"edges": edges}}}}


def test_extract_links_returns_urls_and_last_cursor(scraper):
    data = _make_edges(("123", "C1"), ("456", "C2"))
    urls, cursor = scraper._extract_links(data)
    assert len(urls) == 2
    assert urls[0].endswith("/123/v2.json")
    assert urls[1].endswith("/456/v2.json")
    assert cursor == "C2"


def test_extract_links_single_item_no_cursor_returns_none(scraper):
    data = {"data": {"search": {"products": {"edges": [{"node": {"id": "99"}}]}}}}
    urls, cursor = scraper._extract_links(data)
    assert urls[0].endswith("/99/v2.json")
    assert cursor is None


def test_extract_links_empty_edges_returns_empty(scraper):
    data = {"data": {"search": {"products": {"edges": []}}}}
    urls, cursor = scraper._extract_links(data)
    assert urls == []
    assert cursor is None


def test_extract_links_missing_data_returns_empty(scraper):
    urls, cursor = scraper._extract_links({})
    assert urls == []
    assert cursor is None


def test_extract_links_node_without_id_is_skipped(scraper):
    data = {"data": {"search": {"products": {"edges": [{"node": {}, "cursor": "X"}]}}}}
    urls, cursor = scraper._extract_links(data)
    assert urls == []
    assert cursor is None


# ---------------------------------------------------------------------------
# search (pagination)
# ---------------------------------------------------------------------------


def test_search_single_page(scraper):
    mock_response = MagicMock()
    with (
        patch.object(scraper, "_get_search_data", return_value=mock_response),
        patch.object(scraper, "_extract_links", return_value=(["url1", "url2"], None)),
    ):
        result = scraper.search("notebook")
    assert result == ["url1", "url2"]


def test_search_multiple_pages_stops_when_no_cursor(scraper):
    mock_response = MagicMock()
    extract_side_effects = [
        (["url1"], "CURSOR1"),
        (["url2"], "CURSOR2"),
        (["url3"], None),
    ]
    with (
        patch.object(
            scraper, "_get_search_data", return_value=mock_response
        ) as mock_get,
        patch.object(scraper, "_extract_links", side_effect=extract_side_effects),
    ):
        result = scraper.search("fone")
    assert result == ["url1", "url2", "url3"]
    assert mock_get.call_count == 3


def test_search_passes_cursor_to_next_page(scraper):
    mock_response = MagicMock()
    calls = []

    def fake_get_search_data(term, after=None):
        calls.append(after)
        return mock_response

    with (
        patch.object(scraper, "_get_search_data", side_effect=fake_get_search_data),
        patch.object(
            scraper,
            "_extract_links",
            side_effect=[
                (["url1"], "NEXT"),
                (["url2"], None),
            ],
        ),
    ):
        scraper.search("test")

    assert calls == [None, "NEXT"]


# ---------------------------------------------------------------------------
# scrape_data
# ---------------------------------------------------------------------------

_SCRAPE_RESPONSE = {
    "canonical_url": "https://pages.enjoei.com.br/products/12345",
    "title": "Controle Gamesir",
    "fallback_pricing": {
        "price": {"listed": "299", "sale": None},
        "state": "published",
    },
    "description": "Novo em caixa",
    "photos": ["abc123photo"],
    "id": "12345",
}


def _make_scrape_page_response(data):
    import json as json_mod
    ctx = AsyncMock()
    ctx.close = AsyncMock()

    text_content_mock = AsyncMock(return_value=json_mod.dumps(data))
    locator_mock = MagicMock(return_value=AsyncMock())
    locator_mock.return_value.text_content = text_content_mock

    page = AsyncMock()
    page.locator = locator_mock
    page.goto = AsyncMock()
    return ctx, page


def test_scrape_data_returns_correct_fields(scraper):
    ctx, page = _make_scrape_page_response(_SCRAPE_RESPONSE)
    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)):
        data = scraper.scrape_data("http://pages.enjoei.com.br/products/12345/v2.json")
    assert data["url"] == "https://pages.enjoei.com.br/products/12345"
    assert data["title"] == "Controle Gamesir"
    assert data["price"] == "299"
    assert data["is_available"] is True
    assert data["source_product_code"].startswith("EJ")
    assert "image_urls" in data
    assert data["description"] == "Novo em caixa"


def test_scrape_data_unavailable_product(scraper):
    payload = {**_SCRAPE_RESPONSE}
    payload["fallback_pricing"] = {"price": {"listed": "0"}, "state": "sold"}
    ctx, page = _make_scrape_page_response(payload)
    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)):
        data = scraper.scrape_data("http://x.com")
    assert data["is_available"] is False


def test_scrape_data_no_photos_yields_empty_image_url(scraper):
    payload = {**_SCRAPE_RESPONSE, "photos": []}
    ctx, page = _make_scrape_page_response(payload)
    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)):
        data = scraper.scrape_data("http://x.com")
    assert data["image_urls"] == ""


def test_scrape_data_uses_sale_price_when_listed_is_none(scraper):
    payload = {**_SCRAPE_RESPONSE}
    payload["fallback_pricing"] = {
        "price": {"listed": None, "sale": "199"},
        "state": "published",
    }
    ctx, page = _make_scrape_page_response(payload)
    with patch.object(scraper, "fetch_page_sync", return_value=(ctx, page)):
        data = scraper.scrape_data("http://x.com")
    assert data["price"] == "199"


# ---------------------------------------------------------------------------
# update_data
# ---------------------------------------------------------------------------


def test_update_data_merges_existing_product_with_fresh_scraped_data(scraper):
    product = {
        "url": "https://www.enjoei.com.br/p/controle-gamesir-12345",
        "id": "7",
        "source_website_id": "2",
    }
    fresh = {"url": "https://pages.enjoei.com.br/products/12345", "price": "350"}
    with patch.object(scraper, "scrape_data", return_value=fresh) as mock_scrape:
        result = scraper.update_data(product)
    # URL extracted from product["url"].split("-")[-1]
    mock_scrape.assert_called_once_with(
        "https://pages.enjoei.com.br/products/12345/v2.json"
    )
    assert result["price"] == "350"
    assert result["id"] == "7"  # original field preserved from merge
