"""Tests for src/config/free_proxy.py."""

from unittest.mock import MagicMock, patch

import pytest

from src.config.free_proxy import (
    FreeProxy,
    ProxyPool,
    build_proxy_pool,
    fetch_proxy_list,
    validate_proxies,
)

# ---------------------------------------------------------------------------
# FreeProxy
# ---------------------------------------------------------------------------


class TestFreeProxy:
    def test_to_playwright_proxy(self):
        fp = FreeProxy(server="socks5://1.2.3.4:1080", latency_ms=150)
        result = fp.to_playwright_proxy()
        assert result == {"server": "socks5://1.2.3.4:1080"}

    def test_frozen(self):
        fp = FreeProxy(server="socks5://1.2.3.4:1080")
        with pytest.raises(AttributeError):
            fp.server = "changed"


# ---------------------------------------------------------------------------
# ProxyPool
# ---------------------------------------------------------------------------


class TestProxyPool:
    def test_empty_pool(self):
        pool = ProxyPool()
        assert pool.is_empty
        assert pool.size == 0
        assert pool.get_next() is None

    def test_round_robin(self):
        p1 = FreeProxy(server="socks5://a:1")
        p2 = FreeProxy(server="socks5://b:2")
        pool = ProxyPool(proxies=[p1, p2])

        assert pool.get_next() is p1
        assert pool.get_next() is p2
        assert pool.get_next() is p1  # wraps around

    def test_mark_dead_removes(self):
        p1 = FreeProxy(server="socks5://a:1")
        p2 = FreeProxy(server="socks5://b:2")
        pool = ProxyPool(proxies=[p1, p2])

        pool.mark_dead(p1)
        assert pool.size == 1
        assert pool.get_next() is p2

    def test_mark_dead_nonexistent_is_noop(self):
        p1 = FreeProxy(server="socks5://a:1")
        pool = ProxyPool(proxies=[p1])
        pool.mark_dead(FreeProxy(server="socks5://z:9"))
        assert pool.size == 1

    def test_extend_deduplicates(self):
        p1 = FreeProxy(server="socks5://a:1")
        pool = ProxyPool(proxies=[p1])

        new = [
            FreeProxy(server="socks5://a:1"),  # duplicate
            FreeProxy(server="socks5://b:2"),  # new
        ]
        pool.extend(new)
        assert pool.size == 2

    def test_age_minutes_inf_when_not_fetched(self):
        pool = ProxyPool()
        assert pool.age_minutes == float("inf")


# ---------------------------------------------------------------------------
# fetch_proxy_list
# ---------------------------------------------------------------------------


class TestFetchProxyList:
    @patch("src.config.free_proxy.requests.get")
    def test_fetches_from_github_sources(self, mock_get):
        """Should parse newline-separated ip:port from raw text."""
        mock_resp = MagicMock()
        mock_resp.text = "1.2.3.4:1080\n5.6.7.8:9090\n"
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"proxies": []}
        mock_get.return_value = mock_resp

        result = fetch_proxy_list()
        assert "1.2.3.4:1080" in result
        assert "5.6.7.8:9090" in result

    @patch("src.config.free_proxy.requests.get")
    def test_deduplicates(self, mock_get):
        """Same proxy from multiple sources should appear once."""
        mock_resp = MagicMock()
        mock_resp.text = "1.2.3.4:1080\n1.2.3.4:1080\n"
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"proxies": []}
        mock_get.return_value = mock_resp

        result = fetch_proxy_list()
        assert result.count("1.2.3.4:1080") == 1

    @patch("src.config.free_proxy.requests.get", side_effect=Exception("offline"))
    def test_handles_fetch_errors_gracefully(self, mock_get):
        """If all sources fail, return empty list."""
        result = fetch_proxy_list()
        assert result == []


# ---------------------------------------------------------------------------
# validate_proxies
# ---------------------------------------------------------------------------


class TestValidateProxies:
    @patch("src.config.free_proxy._validate_single")
    def test_returns_only_working_proxies(self, mock_validate):
        mock_validate.side_effect = [
            FreeProxy(server="socks5://a:1", latency_ms=100),
            None,  # dead
            FreeProxy(server="socks5://c:3", latency_ms=50),
        ]

        result = validate_proxies(["a:1", "b:2", "c:3"], max_workers=1)
        assert len(result) == 2
        # Sorted by latency
        assert result[0].server == "socks5://c:3"
        assert result[1].server == "socks5://a:1"

    @patch("src.config.free_proxy._validate_single", return_value=None)
    def test_all_dead_returns_empty(self, mock_validate):
        result = validate_proxies(["a:1", "b:2"], max_workers=1)
        assert result == []

    def test_empty_input(self):
        result = validate_proxies([], max_workers=1)
        assert result == []


# ---------------------------------------------------------------------------
# build_proxy_pool
# ---------------------------------------------------------------------------


class TestBuildProxyPool:
    @patch("src.config.free_proxy.validate_proxies")
    @patch("src.config.free_proxy.fetch_proxy_list")
    def test_returns_pool_with_working_proxies(self, mock_fetch, mock_validate):
        mock_fetch.return_value = ["a:1", "b:2"]
        mock_validate.return_value = [FreeProxy(server="socks5://a:1")]

        pool = build_proxy_pool()
        assert pool.size == 1
        assert pool.fetched_at > 0

    @patch("src.config.free_proxy.validate_proxies", return_value=[])
    @patch("src.config.free_proxy.fetch_proxy_list", return_value=[])
    def test_returns_empty_pool_when_nothing_works(self, mock_fetch, mock_validate):
        pool = build_proxy_pool()
        assert pool.is_empty
