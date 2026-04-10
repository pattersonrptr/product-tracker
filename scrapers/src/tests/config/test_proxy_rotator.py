"""Tests for src/config/proxy_rotator.py."""

import time
from unittest.mock import patch

from src.config.free_proxy import FreeProxy, ProxyPool
from src.config.proxy import ProxyConfig
from src.config.proxy_rotator import (
    FreeProxyRotator,
    PaidProxyRotator,
    get_proxy_rotator,
)

# ---------------------------------------------------------------------------
# PaidProxyRotator
# ---------------------------------------------------------------------------


class TestPaidProxyRotator:
    def _make_config(self) -> ProxyConfig:
        return ProxyConfig(
            server="http://proxy.example.com:8080",
            username="user",
            password="pass",
        )

    def test_mode(self):
        rotator = PaidProxyRotator(self._make_config())
        assert rotator.mode == "paid"

    def test_pool_size_always_one(self):
        rotator = PaidProxyRotator(self._make_config())
        assert rotator.pool_size == 1

    def test_next_proxy_returns_playwright_dict(self):
        rotator = PaidProxyRotator(self._make_config())
        proxy = rotator.next_proxy()
        assert proxy["server"] == "http://proxy.example.com:8080"
        assert proxy["username"] == "user"
        assert proxy["password"] == "pass"

    def test_next_proxy_always_same(self):
        rotator = PaidProxyRotator(self._make_config())
        assert rotator.next_proxy() == rotator.next_proxy()

    def test_report_failure_does_not_raise(self):
        rotator = PaidProxyRotator(self._make_config())
        proxy = rotator.next_proxy()
        rotator.report_failure(proxy)  # should not raise
        # Still returns same proxy — paid rotator can't remove it.
        assert rotator.pool_size == 1


# ---------------------------------------------------------------------------
# FreeProxyRotator
# ---------------------------------------------------------------------------


class TestFreeProxyRotator:
    def _make_pool(self, count: int = 5) -> ProxyPool:
        proxies = [FreeProxy(server=f"socks5://host{i}:{i}") for i in range(count)]
        return ProxyPool(proxies=proxies, fetched_at=time.time())

    def test_mode(self):
        rotator = FreeProxyRotator(self._make_pool())
        assert rotator.mode == "free"

    def test_pool_size(self):
        rotator = FreeProxyRotator(self._make_pool(3))
        assert rotator.pool_size == 3

    def test_next_proxy_returns_dict(self):
        rotator = FreeProxyRotator(self._make_pool())
        proxy = rotator.next_proxy()
        assert isinstance(proxy, dict)
        assert "server" in proxy

    def test_next_proxy_rotates(self):
        rotator = FreeProxyRotator(self._make_pool(3))
        servers = [rotator.next_proxy()["server"] for _ in range(6)]
        # Should cycle: 0, 1, 2, 0, 1, 2
        assert servers[0] == servers[3]
        assert servers[1] == servers[4]
        assert servers[2] == servers[5]

    def test_report_failure_removes_proxy(self):
        pool = self._make_pool(3)
        rotator = FreeProxyRotator(pool)
        proxy = rotator.next_proxy()
        rotator.report_failure(proxy)
        assert rotator.pool_size == 2

    def test_report_failure_with_unknown_server_is_noop(self):
        rotator = FreeProxyRotator(self._make_pool(3))
        rotator.report_failure({"server": "socks5://unknown:9999"})
        assert rotator.pool_size == 3

    @patch("src.config.proxy_rotator.build_proxy_pool")
    def test_empty_pool_triggers_refresh(self, mock_build):
        """When pool is empty, next_proxy should attempt to refresh."""
        fresh = self._make_pool(2)
        mock_build.return_value = fresh

        rotator = FreeProxyRotator()  # starts with empty pool
        proxy = rotator.next_proxy()

        mock_build.assert_called_once()
        assert proxy is not None

    @patch("src.config.proxy_rotator.build_proxy_pool")
    def test_small_pool_triggers_refresh(self, mock_build):
        """Pool with fewer than _POOL_MIN_SIZE proxies should trigger refresh."""
        # Start with 2 proxies (< _POOL_MIN_SIZE=3).
        small_pool = ProxyPool(
            proxies=[
                FreeProxy(server="socks5://a:1"),
                FreeProxy(server="socks5://b:2"),
            ],
            fetched_at=time.time(),
        )
        fresh = ProxyPool(
            proxies=[FreeProxy(server="socks5://c:3")],
            fetched_at=time.time(),
        )
        mock_build.return_value = fresh

        rotator = FreeProxyRotator(small_pool)
        rotator.next_proxy()

        mock_build.assert_called_once()
        # Should have merged: 2 existing + 1 new = 3
        assert rotator.pool_size == 3

    @patch("src.config.proxy_rotator.build_proxy_pool")
    def test_old_pool_triggers_refresh(self, mock_build):
        """Pool older than _POOL_MAX_AGE_MINUTES should trigger refresh."""
        old_pool = self._make_pool(5)
        old_pool.fetched_at = time.time() - (31 * 60)  # 31 minutes ago

        mock_build.return_value = ProxyPool(proxies=[], fetched_at=time.time())

        rotator = FreeProxyRotator(old_pool)
        rotator.next_proxy()

        mock_build.assert_called_once()

    @patch("src.config.proxy_rotator.build_proxy_pool")
    def test_fresh_large_pool_no_refresh(self, mock_build):
        """A fresh pool with enough proxies should NOT trigger refresh."""
        rotator = FreeProxyRotator(self._make_pool(10))
        rotator.next_proxy()

        mock_build.assert_not_called()

    @patch("src.config.proxy_rotator.build_proxy_pool")
    def test_next_proxy_none_when_pool_stays_empty(self, mock_build):
        """If refresh also returns nothing, next_proxy returns None."""
        mock_build.return_value = ProxyPool()

        rotator = FreeProxyRotator()  # empty
        result = rotator.next_proxy()
        assert result is None


# ---------------------------------------------------------------------------
# get_proxy_rotator
# ---------------------------------------------------------------------------


class TestGetProxyRotator:
    @patch("src.config.proxy_rotator.load_proxy_config")
    def test_returns_paid_when_env_set(self, mock_load):
        mock_load.return_value = ProxyConfig(
            server="http://paid:8080",
            username="u",
            password="p",
        )
        rotator = get_proxy_rotator()
        assert isinstance(rotator, PaidProxyRotator)
        assert rotator.mode == "paid"

    @patch("src.config.proxy_rotator.load_proxy_config", return_value=None)
    def test_returns_free_when_no_paid(self, mock_load):
        rotator = get_proxy_rotator()
        assert isinstance(rotator, FreeProxyRotator)
        assert rotator.mode == "free"
