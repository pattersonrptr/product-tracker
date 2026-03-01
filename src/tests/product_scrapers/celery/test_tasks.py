"""
Tests for src/product_scrapers/celery/tasks.py.

Strategy: All external I/O (HTTP via requests, Celery task dispatch,
ScraperFactory/ScraperManager) is mocked so these tests run without any
running infrastructure.
"""

from typing import cast
from unittest.mock import MagicMock, patch

import requests

from src.product_scrapers.celery.tasks import (
    _finish_log,
    get_celery_worker_token,
    process_urls_list,
    run_scraper_search,
    run_scraper_update,
    run_search,
    save_products,
    scrape_product_page,
    update_product,
    update_products,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(status_code: int, json_data=None):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


def _token_response(token: str = "test_jwt_token"):
    """Build the JSON:API login response that the API returns."""
    return {"data": {"attributes": {"access_token": token}}}


def _make_client_mock(token="test_jwt_token"):
    client = MagicMock()
    client.create_search_execution_log.return_value = {"id": "42"}
    client.get_existing_product_urls.return_value = set()
    client.get_source_website_by_name.return_value = {"id": "2"}
    return client


# ---------------------------------------------------------------------------
# get_celery_worker_token
# ---------------------------------------------------------------------------


@patch("requests.post")
def test_get_celery_worker_token_success(mock_post):
    mock_post.return_value = _mock_response(200, _token_response("abc.jwt.token"))
    token = get_celery_worker_token()
    assert token == "abc.jwt.token"


@patch("requests.post")
def test_get_celery_worker_token_parses_jsonapi_path(mock_post):
    """Regression: must read data.attributes.access_token, not root key."""
    payload = {"data": {"attributes": {"access_token": "deep_token"}}}
    mock_post.return_value = _mock_response(200, payload)
    assert get_celery_worker_token() == "deep_token"


@patch("requests.post")
def test_get_celery_worker_token_fallback_to_plain_json(mock_post):
    """Fallback: if JSON:API path is absent, try root-level access_token."""
    mock_post.return_value = _mock_response(200, {"access_token": "plain_token"})
    assert get_celery_worker_token() == "plain_token"


@patch("requests.post")
def test_get_celery_worker_token_returns_none_on_http_error(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException("connection refused")
    assert get_celery_worker_token() is None


@patch("requests.post")
def test_get_celery_worker_token_returns_none_when_token_missing(mock_post):
    mock_post.return_value = _mock_response(200, {"data": {"attributes": {}}})
    # Both paths return falsy → token is None / ""
    result = get_celery_worker_token()
    assert not result


# ---------------------------------------------------------------------------
# run_search
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
@patch("src.product_scrapers.celery.tasks.process_urls_list")
def test_run_search_success(
    mock_process, mock_manager_cls, mock_factory_cls, mock_client_cls, mock_token
):
    client = _make_client_mock()
    mock_client_cls.return_value = client

    mock_scraper_instance = MagicMock()
    mock_factory_cls.return_value.create_scraper.return_value = mock_scraper_instance

    mock_manager = MagicMock()
    mock_manager.get_products_urls.return_value = ["url1", "url2", "url3"]
    mock_manager.get_urls_to_update.return_value = ["url1", "url2", "url3"]
    mock_manager_cls.return_value = mock_manager

    mock_process.apply_async = MagicMock()

    result = run_search("notebook", "enjoei", 1)

    assert result["status"] == "success"
    assert result["new_urls_count"] == 3
    client.create_search_execution_log.assert_called_once_with(
        search_config_id=1, status="running"
    )


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
def test_run_search_scraper_exception_logs_failed(
    mock_manager_cls, mock_factory_cls, mock_client_cls, mock_token
):
    client = _make_client_mock()
    mock_client_cls.return_value = client
    mock_factory_cls.return_value.create_scraper.side_effect = ValueError(
        "not supported"
    )

    result = run_search("x", "bad_scraper", 1)

    assert result["status"] == "error"
    # Should create a "failed" log with error_message
    failed_call = [
        c
        for c in client.create_search_execution_log.call_args_list
        if c.kwargs.get("status") == "failed" or (c.args and "failed" in c.args)
    ]
    assert len(failed_call) >= 1


# ---------------------------------------------------------------------------
# save_products
# ---------------------------------------------------------------------------


def _scrape_result(url: str, price: float = 99.0):
    return {
        "status": "success",
        "data": {
            "url": url,
            "title": "Test Product",
            "price": price,
            "current_price": price,
            "source_website_id": "2",
        },
    }


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_save_products_creates_new_products(mock_client_cls, mock_token):
    client = _make_client_mock()
    client.get_product_by_url.return_value = {}  # product does not exist yet
    client.create_product.return_value = {"id": "10"}
    mock_client_cls.return_value = client

    results = [
        _scrape_result("http://a.com", 50.0),
        _scrape_result("http://b.com", 75.0),
    ]
    outcome = save_products(results, "enjoei", search_config_id=1, log_id="42")

    assert outcome["status"] == "success"
    assert outcome["created"] == 2
    assert outcome["processed"] == 2
    assert client.create_product.call_count == 2
    assert client.create_price_history.call_count == 2


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_save_products_updates_existing_products(mock_client_cls, mock_token):
    client = _make_client_mock()
    client.get_product_by_url.return_value = {"id": "5"}  # product exists
    mock_client_cls.return_value = client

    results = [_scrape_result("http://a.com", 120.0)]
    outcome = save_products(results, "enjoei", search_config_id=1)

    assert outcome["created"] == 0
    client.update_product.assert_called_once()
    client.create_price_history.assert_called_once_with("5", 120.0)


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_save_products_empty_results_returns_error(mock_client_cls, mock_token):
    client = _make_client_mock()
    mock_client_cls.return_value = client

    outcome = save_products([], "enjoei", search_config_id=1)
    assert outcome["status"] == "error"
    assert outcome["message"] == "No products to save"


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_save_products_all_failed_scrapes(mock_client_cls, mock_token):
    client = _make_client_mock()
    mock_client_cls.return_value = client

    results = [
        {"status": "error", "url": "http://a.com", "message": "timeout"},
        {"status": "error", "url": "http://b.com", "message": "timeout"},
    ]
    outcome = save_products(results, "enjoei", search_config_id=1)
    assert outcome["status"] == "error"
    assert outcome["message"] == "All scraping attempts failed"


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_save_products_skips_result_without_url(mock_client_cls, mock_token):
    client = _make_client_mock()
    mock_client_cls.return_value = client

    results = [
        {
            "status": "success",
            "data": {
                "title": "No URL product",
                "current_price": 10.0,
                "source_website_id": "2",
            },
        }
    ]
    outcome = save_products(results, "enjoei", search_config_id=1)
    assert outcome["created"] == 0


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_save_products_no_price_skips_price_history(mock_client_cls, mock_token):
    client = _make_client_mock()
    client.get_product_by_url.return_value = {}
    client.create_product.return_value = {"id": "11"}
    mock_client_cls.return_value = client

    results = [
        {
            "status": "success",
            "data": {"url": "http://a.com", "title": "X", "source_website_id": "2"},
        }
        # No current_price
    ]
    outcome = save_products(results, "enjoei", search_config_id=1)
    assert outcome["created"] == 1
    client.create_price_history.assert_not_called()


# ---------------------------------------------------------------------------
# _finish_log
# ---------------------------------------------------------------------------


def test_finish_log_calls_create_execution_log():
    client = MagicMock()
    _finish_log(
        client, search_config_id=1, log_id="42", status="success", results_count=10
    )
    client.create_search_execution_log.assert_called_once_with(
        search_config_id=1, status="success", results_count=10, error_message=None
    )


def test_finish_log_with_error_message():
    client = MagicMock()
    _finish_log(
        client,
        search_config_id=2,
        log_id=None,
        status="failed",
        results_count=0,
        error_message="scrape failed",
    )
    client.create_search_execution_log.assert_called_once_with(
        search_config_id=2,
        status="failed",
        results_count=0,
        error_message="scrape failed",
    )


def test_finish_log_does_nothing_when_search_config_id_is_none():
    client = MagicMock()
    _finish_log(
        client, search_config_id=None, log_id=None, status="success", results_count=0
    )
    client.create_search_execution_log.assert_not_called()


# ---------------------------------------------------------------------------
# run_scraper_search
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_run_scraper_search_config_not_found(mock_client_cls, mock_token):
    client = MagicMock()
    client.get_search_config_by_id.return_value = None
    mock_client_cls.return_value = client

    result = run_scraper_search(999)
    assert result["status"] == "error"
    assert "999" in result["message"]


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.requests")
@patch("src.product_scrapers.celery.tasks.group")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_run_scraper_search_dispatches_active_source_websites(
    mock_client_cls, mock_group, mock_requests, mock_token
):
    client = MagicMock()
    client.get_search_config_by_id.return_value = {
        "search_term": "notebook",
        "source_website_ids": [1, 2],
    }
    client.base_url = "http://web:8000"
    client.headers = {}
    mock_client_cls.return_value = client

    # site 1 is active, site 2 is inactive
    def _sw_response(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "source-websites/1" in url:
            resp.json.return_value = {
                "data": {"attributes": {"name": "enjoei", "is_active": True}}
            }
        else:
            resp.json.return_value = {
                "data": {"attributes": {"name": "olx", "is_active": False}}
            }
        return resp

    mock_requests.get.side_effect = _sw_response

    mock_group_instance = MagicMock()
    mock_group.return_value = mock_group_instance
    mock_group_instance.return_value = {"dispatched": True}

    run_scraper_search(1)

    mock_group.assert_called_once()


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.requests")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_run_scraper_search_no_active_websites_returns_skipped(
    mock_client_cls, mock_requests, mock_token
):
    client = MagicMock()
    client.get_search_config_by_id.return_value = {
        "search_term": "notebook",
        "source_website_ids": [1],
    }
    client.base_url = "http://web:8000"
    client.headers = {}
    mock_client_cls.return_value = client

    # _extract_attributes is a static method — patch it on the class mock
    mock_client_cls._extract_attributes.return_value = {
        "name": "olx",
        "is_active": False,
    }

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": {"attributes": {"name": "olx", "is_active": False}}
    }
    mock_requests.get.return_value = resp

    result = run_scraper_search(1)
    assert result["status"] == "skipped"


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.requests")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_run_scraper_search_non_200_source_website_skipped(
    mock_client_cls, mock_requests, mock_token
):
    client = MagicMock()
    client.get_search_config_by_id.return_value = {
        "search_term": "cadeira",
        "source_website_ids": [5],
    }
    client.base_url = "http://web:8000"
    client.headers = {}
    mock_client_cls.return_value = client

    resp = MagicMock()
    resp.status_code = 404
    mock_requests.get.return_value = resp

    result = run_scraper_search(1)
    assert result["status"] == "skipped"


# ---------------------------------------------------------------------------
# process_urls_list
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
@patch("src.product_scrapers.celery.tasks.group")
def test_process_urls_list_splits_and_dispatches(
    mock_group, mock_manager_cls, mock_factory_cls
):
    mock_scraper = MagicMock()
    mock_factory_cls.return_value.create_scraper.return_value = mock_scraper

    mock_manager = MagicMock()
    mock_manager.split_search_urls.return_value = [["url1", "url2"]]
    mock_manager_cls.return_value = mock_manager

    mock_task_group = MagicMock()
    mock_group.return_value = mock_task_group
    mock_task_group.apply_async.return_value = {"dispatched": True}

    search_results = {"status": "success", "urls": ["url1", "url2"]}
    process_urls_list(search_results, "enjoei", search_config_id=1, log_id="42")

    mock_manager.split_search_urls.assert_called_once_with(search_results, 100)


# ---------------------------------------------------------------------------
# scrape_product_page
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
def test_scrape_product_page_success(mock_manager_cls, mock_factory_cls):
    mock_scraper = MagicMock()
    mock_factory_cls.return_value.create_scraper.return_value = mock_scraper

    mock_manager = MagicMock()
    mock_manager.scrape_product.return_value = {
        "title": "Cool Book",
        "current_price": 25.0,
    }
    mock_manager_cls.return_value = mock_manager

    result = scrape_product_page("http://enjoei.com.br/produto/1", "enjoei")
    result_dict = cast(dict, result)
    assert result_dict["status"] == "success"
    assert result_dict["data"]["title"] == "Cool Book"


@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
def test_scrape_product_page_exception_returns_error(
    mock_manager_cls, mock_factory_cls
):
    mock_scraper = MagicMock()
    mock_factory_cls.return_value.create_scraper.return_value = mock_scraper

    mock_manager = MagicMock()
    mock_manager.scrape_product.side_effect = Exception("page not found")
    mock_manager_cls.return_value = mock_manager

    result = scrape_product_page("http://enjoei.com.br/produto/bad", "enjoei")
    assert result["status"] == "error"
    assert result["url"] == "http://enjoei.com.br/produto/bad"
    assert "page not found" in result["message"]


# ---------------------------------------------------------------------------
# run_scraper_update
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_run_scraper_update_no_products_returns_skipped(mock_client_cls, mock_token):
    client = MagicMock()
    client.get_products.return_value = []
    mock_client_cls.return_value = client

    result = run_scraper_update("enjoei")
    assert result["status"] == "skipped"


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.chord")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_run_scraper_update_dispatches_chord_for_products(
    mock_client_cls, mock_chord, mock_token
):
    client = MagicMock()
    client.get_products.return_value = [{"id": "1"}, {"id": "2"}]
    mock_client_cls.return_value = client

    mock_chord_instance = MagicMock()
    mock_chord.return_value = mock_chord_instance
    mock_chord_instance.return_value = {"dispatched": True}

    run_scraper_update("enjoei")

    mock_chord.assert_called_once()


# ---------------------------------------------------------------------------
# update_product
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
def test_update_product_success(mock_manager_cls, mock_factory_cls):
    mock_scraper = MagicMock()
    mock_factory_cls.return_value.create_scraper.return_value = mock_scraper

    mock_manager = MagicMock()
    mock_manager.update_product.return_value = {
        "title": "Updated",
        "current_price": 30.0,
    }
    mock_manager_cls.return_value = mock_manager

    result = update_product({"id": "7", "url": "http://a.com"}, "enjoei")
    assert result["status"] == "success"
    assert result["data"]["title"] == "Updated"


@patch("src.product_scrapers.celery.tasks.ScraperFactory")
@patch("src.product_scrapers.celery.tasks.ScraperManager")
def test_update_product_exception_returns_error(mock_manager_cls, mock_factory_cls):
    mock_scraper = MagicMock()
    mock_factory_cls.return_value.create_scraper.return_value = mock_scraper

    mock_manager = MagicMock()
    mock_manager.update_product.side_effect = Exception("scrape error")
    mock_manager_cls.return_value = mock_manager

    result = update_product({"id": "7", "url": "http://a.com"}, "enjoei")
    assert result["status"] == "error"
    assert result["url"] == "http://a.com"


# ---------------------------------------------------------------------------
# update_products
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_update_products_empty_results_returns_error(mock_client_cls, mock_token):
    client = MagicMock()
    mock_client_cls.return_value = client

    result = update_products([], "enjoei")
    assert result["status"] == "error"
    assert result["message"] == "No products to update"


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_update_products_all_failed_returns_error(mock_client_cls, mock_token):
    client = MagicMock()
    client.get_source_website_by_name.return_value = {"id": "2"}
    mock_client_cls.return_value = client

    results = [
        {"status": "error", "url": "http://a.com", "message": "fail"},
    ]
    result = update_products(results, "enjoei")
    assert result["status"] == "error"
    assert result["message"] == "All update attempts failed"


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_update_products_updates_and_records_price_history(mock_client_cls, mock_token):
    client = MagicMock()
    client.get_source_website_by_name.return_value = {"id": "2"}
    client.update_product.return_value = {"id": "5"}
    mock_client_cls.return_value = client

    results = [
        {
            "status": "success",
            "data": {
                "id": "5",
                "title": "Item",
                "current_price": 45.0,
                "source_website_id": "2",
            },
        }
    ]
    result = update_products(results, "enjoei")
    assert result["status"] == "success"
    assert result["updated"] == 1
    client.update_product.assert_called_once()
    client.create_price_history.assert_called_once_with("5", 45.0)


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_update_products_skips_entry_without_product_id(mock_client_cls, mock_token):
    client = MagicMock()
    client.get_source_website_by_name.return_value = {"id": "2"}
    mock_client_cls.return_value = client

    results = [
        {
            "status": "success",
            "data": {"title": "No ID", "current_price": 10.0, "source_website_id": "2"},
        }
    ]
    result = update_products(results, "enjoei")
    assert result["updated"] == 0
    client.update_product.assert_not_called()


@patch("src.product_scrapers.celery.tasks.get_celery_worker_token", return_value="tok")
@patch("src.product_scrapers.celery.tasks.ApiClient")
def test_update_products_no_price_skips_price_history(mock_client_cls, mock_token):
    client = MagicMock()
    client.get_source_website_by_name.return_value = {"id": "2"}
    client.update_product.return_value = {"id": "9"}
    mock_client_cls.return_value = client

    results = [
        {
            "status": "success",
            "data": {"id": "9", "title": "Item", "source_website_id": "2"},
            # No current_price
        }
    ]
    result = update_products(results, "enjoei")
    assert result["updated"] == 1
    client.create_price_history.assert_not_called()
