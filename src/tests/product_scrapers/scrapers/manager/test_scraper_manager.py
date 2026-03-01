from unittest.mock import MagicMock

import pytest

from src.product_scrapers.scrapers.manager.scraper_manager import ScraperManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_scraper():
    scraper = MagicMock()
    scraper.__str__ = MagicMock(return_value="MockScraper")
    scraper.search.return_value = ["url1", "url2", "url3"]
    scraper.scrape_data.return_value = {"url": "url1", "title": "Product A"}
    scraper.update_data.return_value = {"url": "url1", "title": "Updated A"}
    return scraper


@pytest.fixture
def manager(mock_scraper):
    return ScraperManager(scraper=mock_scraper)


# ---------------------------------------------------------------------------
# get_products_urls
# ---------------------------------------------------------------------------


def test_get_products_urls_delegates_to_scraper(manager, mock_scraper):
    result = manager.get_products_urls("notebook")
    mock_scraper.search.assert_called_once_with("notebook")
    assert result == ["url1", "url2", "url3"]


def test_get_products_urls_returns_empty_list_when_scraper_returns_none(mock_scraper):
    mock_scraper.search.return_value = []
    manager = ScraperManager(mock_scraper)
    assert manager.get_products_urls("nothing") == []


# ---------------------------------------------------------------------------
# scrape_product
# ---------------------------------------------------------------------------


def test_scrape_product_delegates_to_scraper(manager, mock_scraper):
    result = manager.scrape_product("url1")
    mock_scraper.scrape_data.assert_called_once_with("url1")
    assert result == {"url": "url1", "title": "Product A"}


# ---------------------------------------------------------------------------
# update_product
# ---------------------------------------------------------------------------


def test_update_product_delegates_to_scraper(manager, mock_scraper):
    product = {"url": "url1", "id": "10"}
    result = manager.update_product(product)
    mock_scraper.update_data.assert_called_once_with(product)
    assert result == {"url": "url1", "title": "Updated A"}


# ---------------------------------------------------------------------------
# get_urls_to_update (static)
# ---------------------------------------------------------------------------


def test_get_urls_to_update_returns_new_only():
    existing = {"url1", "url2"}
    all_urls = ["url1", "url2", "url3", "url4"]
    result = ScraperManager.get_urls_to_update(existing, all_urls)
    assert set(result) == {"url3", "url4"}


def test_get_urls_to_update_no_new_urls():
    existing = {"url1", "url2"}
    result = ScraperManager.get_urls_to_update(existing, ["url1", "url2"])
    assert result == []


def test_get_urls_to_update_all_new():
    result = ScraperManager.get_urls_to_update(set(), ["a", "b", "c"])
    assert set(result) == {"a", "b", "c"}


def test_get_urls_to_update_empty_inputs():
    assert ScraperManager.get_urls_to_update(set(), []) == []


# ---------------------------------------------------------------------------
# split_search_urls / _get_search_urls / _chunk_urls
# ---------------------------------------------------------------------------


def test_split_search_urls_returns_correct_chunks(manager):
    search_results = {"search": "book", "urls": ["a", "b", "c", "d", "e"]}
    chunks = list(manager.split_search_urls(search_results, chunk_size=2))
    assert chunks == [["a", "b"], ["c", "d"], ["e"]]


def test_split_search_urls_chunk_larger_than_list(manager):
    search_results = {"search": "book", "urls": ["a", "b"]}
    chunks = list(manager.split_search_urls(search_results, chunk_size=10))
    assert chunks == [["a", "b"]]


def test_split_search_urls_empty_urls(manager):
    search_results = {"search": "book", "urls": []}
    chunks = list(manager.split_search_urls(search_results, chunk_size=5))
    assert chunks == []


def test_get_search_urls_extracts_url_list():
    search_results = {"search": "laptop", "urls": ["x", "y"]}
    assert ScraperManager._get_search_urls(search_results) == ["x", "y"]


def test_chunk_urls_exact_multiple():
    chunks = list(ScraperManager._chunk_urls(["a", "b", "c", "d"], chunk_size=2))
    assert chunks == [["a", "b"], ["c", "d"]]


def test_chunk_urls_single_item():
    chunks = list(ScraperManager._chunk_urls(["only"], chunk_size=5))
    assert chunks == [["only"]]
