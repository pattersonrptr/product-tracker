"""Proxy configuration loaded from environment variables.

Environment variables
---------------------
``PROXY_SERVER``   – Proxy URL, e.g. ``http://gate.smartproxy.com:7000``
``PROXY_USERNAME`` – (optional) proxy auth username
``PROXY_PASSWORD`` – (optional) proxy auth password
``PROXY_ENABLED``  – Set to ``true`` / ``1`` to activate proxy support
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_TRUTHY = frozenset({"1", "true", "yes"})


@dataclass(frozen=True, slots=True)
class ProxyConfig:
    """Immutable proxy settings."""

    server: str
    username: str | None = None
    password: str | None = None

    def to_playwright_proxy(self) -> dict[str, Any]:
        """Return a dict suitable for Playwright's *proxy* kwarg.

        Example return::

            {"server": "http://host:7000", "username": "u", "password": "p"}
        """
        proxy: dict[str, Any] = {"server": self.server}
        if self.username:
            proxy["username"] = self.username
        if self.password:
            proxy["password"] = self.password
        return proxy


def load_proxy_config() -> ProxyConfig | None:
    """Build a :class:`ProxyConfig` from the environment.

    Returns ``None`` when the proxy is disabled or not configured.
    """
    enabled = os.getenv("PROXY_ENABLED", "").strip().lower() in _TRUTHY
    server = os.getenv("PROXY_SERVER", "").strip()

    if not enabled:
        return None

    if not server:
        logger.warning(
            "PROXY_ENABLED is set but PROXY_SERVER is empty — proxy disabled"
        )
        return None

    username = os.getenv("PROXY_USERNAME", "").strip() or None
    password = os.getenv("PROXY_PASSWORD", "").strip() or None

    logger.info("Proxy enabled: server=%s, auth=%s", server, bool(username))
    return ProxyConfig(server=server, username=username, password=password)
