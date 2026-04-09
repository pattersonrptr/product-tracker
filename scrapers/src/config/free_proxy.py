"""Fetch and validate free SOCKS5 proxies for scraper rotation.

Free proxies are unreliable — many are dead or blocked.  This module
fetches from multiple public sources, validates them in parallel, and
returns only the ones that actually work.

**Why SOCKS5?**  HTTP proxies from free lists are almost universally
blocked by Mercado Livre (0/240 in testing).  SOCKS5 proxies from
residential-looking ranges pass at ~5% rate, which is enough when we
fetch hundreds and only need a handful.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

# Public sources for free SOCKS5 proxy lists.
_SOCKS5_SOURCES: list[str] = [
    # TheSpeedX maintains a large, frequently updated list.
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    # monosans/proxy-list — another well-maintained list.
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
]

# ProxyScrape offers a JSON API with protocol filtering.
_PROXYSCRAPE_URL = (
    "https://api.proxyscrape.com/v4/free-proxy-list/get"
    "?request=display_proxies"
    "&proxy_format=protocolipport"
    "&format=json"
    "&limit=200"
    "&protocol=socks4"
    "&timeout=10000"
)

# Used for fast validation: a well-known URL that returns quickly.
_VALIDATION_URL = "https://httpbin.org/ip"
_VALIDATION_TIMEOUT = 8  # seconds


@dataclass(frozen=True, slots=True)
class FreeProxy:
    """A single free SOCKS5 proxy."""

    server: str  # e.g. "socks5://1.2.3.4:1080"
    latency_ms: int = 0  # response time during validation

    def to_playwright_proxy(self) -> dict[str, str]:
        """Return a dict suitable for Playwright's *proxy* kwarg."""
        return {"server": self.server}


@dataclass
class ProxyPool:
    """A pool of validated free proxies with round-robin iteration."""

    proxies: list[FreeProxy] = field(default_factory=list)
    _index: int = field(default=0, repr=False)
    fetched_at: float = field(default=0.0, repr=False)

    @property
    def size(self) -> int:
        return len(self.proxies)

    @property
    def is_empty(self) -> bool:
        return len(self.proxies) == 0

    @property
    def age_minutes(self) -> float:
        """Minutes since the pool was last fetched."""
        if self.fetched_at == 0:
            return float("inf")
        return (time.time() - self.fetched_at) / 60

    def get_next(self) -> FreeProxy | None:
        """Return the next proxy in round-robin order, or *None*."""
        if not self.proxies:
            return None
        proxy = self.proxies[self._index % len(self.proxies)]
        self._index += 1
        return proxy

    def mark_dead(self, proxy: FreeProxy) -> None:
        """Remove a proxy from the pool."""
        try:
            self.proxies.remove(proxy)
            logger.debug(
                "Removed dead proxy: %s (%d left)", proxy.server, len(self.proxies)
            )
        except ValueError:
            pass  # already removed

    def extend(self, new_proxies: list[FreeProxy]) -> None:
        """Add proxies that aren't already in the pool."""
        existing = {p.server for p in self.proxies}
        added = 0
        for p in new_proxies:
            if p.server not in existing:
                self.proxies.append(p)
                existing.add(p.server)
                added += 1
        if added:
            logger.info(
                "Added %d new proxies to pool (total: %d)", added, len(self.proxies)
            )


def fetch_proxy_list() -> list[str]:
    """Fetch raw SOCKS5 proxy strings from all public sources.

    Returns a deduplicated list of ``"ip:port"`` strings.
    """
    raw: set[str] = set()

    # --- GitHub raw text lists ---
    for source_url in _SOCKS5_SOURCES:
        try:
            resp = requests.get(source_url, timeout=10)
            resp.raise_for_status()
            lines = [
                line.strip()
                for line in resp.text.strip().splitlines()
                if line.strip() and not line.startswith("#")
            ]
            raw.update(lines)
            logger.info(
                "Fetched %d proxies from %s", len(lines), source_url.split("/")[-1]
            )
        except Exception:
            logger.warning(
                "Failed to fetch proxy list from %s", source_url, exc_info=True
            )

    # --- ProxyScrape JSON API (SOCKS4 — many work as SOCKS5 too) ---
    try:
        resp = requests.get(_PROXYSCRAPE_URL, timeout=10)
        data = resp.json()
        for entry in data.get("proxies", []):
            ip = entry.get("ip")
            port = entry.get("port")
            if ip and port:
                raw.add(f"{ip}:{port}")
        logger.info(
            "Fetched %d proxies from ProxyScrape",
            len(data.get("proxies", [])),
        )
    except Exception:
        logger.warning("Failed to fetch from ProxyScrape", exc_info=True)

    logger.info("Total raw proxies (deduplicated): %d", len(raw))
    return list(raw)


def _validate_single(
    proxy_str: str,
    validation_url: str = _VALIDATION_URL,
    timeout: int = _VALIDATION_TIMEOUT,
) -> FreeProxy | None:
    """Test a single proxy.  Returns a :class:`FreeProxy` or *None*."""
    socks_url = f"socks5://{proxy_str}"
    try:
        start = time.monotonic()
        resp = requests.get(
            validation_url,
            proxies={"http": socks_url, "https": socks_url},
            timeout=timeout,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code == 200:
            return FreeProxy(server=socks_url, latency_ms=elapsed_ms)
    except Exception:
        pass
    return None


def validate_proxies(
    raw_proxies: list[str],
    *,
    max_workers: int = 30,
    validation_url: str = _VALIDATION_URL,
    timeout: int = _VALIDATION_TIMEOUT,
) -> list[FreeProxy]:
    """Validate proxies in parallel, return only working ones.

    Proxies are sorted by latency (fastest first).
    """
    working: list[FreeProxy] = []

    logger.info("Validating %d proxies with %d workers…", len(raw_proxies), max_workers)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_validate_single, p, validation_url, timeout): p
            for p in raw_proxies
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                working.append(result)

    working.sort(key=lambda p: p.latency_ms)
    logger.info(
        "Validation complete: %d/%d proxies working (%.1f%%)",
        len(working),
        len(raw_proxies),
        (len(working) / len(raw_proxies) * 100) if raw_proxies else 0,
    )
    return working


def build_proxy_pool(
    *,
    max_workers: int = 30,
    validation_url: str = _VALIDATION_URL,
    timeout: int = _VALIDATION_TIMEOUT,
) -> ProxyPool:
    """Fetch, validate, and return a ready-to-use :class:`ProxyPool`.

    This is the main entry point — call it to get a pool of working
    SOCKS5 proxies.
    """
    raw = fetch_proxy_list()
    working = validate_proxies(
        raw,
        max_workers=max_workers,
        validation_url=validation_url,
        timeout=timeout,
    )
    return ProxyPool(proxies=working, fetched_at=time.time())
