"""Unified proxy management — paid (env var) or free (pool rotation).

This module provides a single interface for the scraper base class.
It checks environment variables first (paid proxy); if none are set,
it falls back to fetching and rotating free SOCKS5 proxies.

Usage in PlaywrightScraper::

    rotator = get_proxy_rotator()        # returns None if nothing available
    proxy_dict = rotator.next_proxy()    # Playwright-compatible dict
    rotator.report_failure(proxy_dict)   # marks current proxy as dead
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from src.config.free_proxy import ProxyPool, build_proxy_pool
from src.config.proxy import ProxyConfig, load_proxy_config

logger = logging.getLogger(__name__)

# Re-fetch free proxies when the pool is older than this.
_POOL_MAX_AGE_MINUTES = 30

# Minimum pool size before triggering an automatic refresh.
_POOL_MIN_SIZE = 3


class PaidProxyRotator:
    """Wraps a single paid proxy from environment variables.

    No rotation — always returns the same proxy.  Never expires.
    """

    def __init__(self, config: ProxyConfig) -> None:
        self._config = config

    def next_proxy(self) -> dict[str, Any]:
        """Return the paid proxy dict for Playwright."""
        return self._config.to_playwright_proxy()

    def report_failure(self, proxy: dict[str, Any]) -> None:
        """Log the failure — can't rotate, nothing to remove."""
        logger.warning("Paid proxy failed: %s", proxy.get("server"))

    @property
    def pool_size(self) -> int:
        return 1

    @property
    def mode(self) -> str:
        return "paid"


class FreeProxyRotator:
    """Rotates through a pool of free SOCKS5 proxies.

    Automatically refreshes the pool when it gets too small or too old.
    Thread-safe.
    """

    def __init__(self, pool: ProxyPool | None = None) -> None:
        self._pool = pool or ProxyPool()
        self._lock = threading.Lock()
        self._refreshing = False

    def _ensure_pool(self) -> None:
        """Refresh the pool if needed (too old or too small)."""
        needs_refresh = (
            self._pool.is_empty
            or self._pool.size < _POOL_MIN_SIZE
            or self._pool.age_minutes > _POOL_MAX_AGE_MINUTES
        )
        if needs_refresh and not self._refreshing:
            self._refresh()

    def _refresh(self) -> None:
        """Fetch and validate a new batch of proxies."""
        with self._lock:
            if self._refreshing:
                return
            self._refreshing = True

        try:
            logger.info("Refreshing free proxy pool…")
            new_pool = build_proxy_pool()
            with self._lock:
                if new_pool.size > 0:
                    # Merge new proxies into existing pool.
                    self._pool.extend(new_pool.proxies)
                    self._pool.fetched_at = time.time()
                    logger.info("Pool refreshed: %d proxies available", self._pool.size)
                else:
                    logger.warning("Refresh returned 0 working proxies")
        finally:
            with self._lock:
                self._refreshing = False

    def next_proxy(self) -> dict[str, str] | None:
        """Return the next proxy dict for Playwright, or *None*."""
        self._ensure_pool()
        with self._lock:
            fp = self._pool.get_next()
        if fp is None:
            logger.warning("No free proxies available")
            return None
        return fp.to_playwright_proxy()

    def report_failure(self, proxy: dict[str, Any]) -> None:
        """Mark a proxy as dead and remove it from the pool."""
        server = proxy.get("server", "")
        with self._lock:
            for fp in list(self._pool.proxies):
                if fp.server == server:
                    self._pool.mark_dead(fp)
                    break
        logger.debug("Proxy marked dead: %s (%d remaining)", server, self._pool.size)

    @property
    def pool_size(self) -> int:
        return self._pool.size

    @property
    def mode(self) -> str:
        return "free"


def get_proxy_rotator() -> PaidProxyRotator | FreeProxyRotator | None:
    """Return the appropriate proxy rotator.

    Priority:
    1. **Paid proxy** (``PROXY_ENABLED=true`` + ``PROXY_SERVER`` set) →
       :class:`PaidProxyRotator`
    2. **Free proxy pool** → :class:`FreeProxyRotator` (fetches on first
       call to ``next_proxy()``)
    3. **None** if explicitly disabled

    The free rotator is returned by default so that scrapers with
    ``_USE_PROXY = True`` always have a chance of getting a working
    proxy without any configuration.
    """
    # Check for paid proxy first.
    paid_config = load_proxy_config()
    if paid_config is not None:
        logger.info("Using paid proxy: %s", paid_config.server)
        return PaidProxyRotator(paid_config)

    # Fall back to free proxy rotation.
    logger.info("No paid proxy configured — using free SOCKS5 proxy rotation")
    return FreeProxyRotator()
