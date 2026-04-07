import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import cloudscraper
import requests

logger = logging.getLogger(__name__)


class RequestScraper(ABC):
    """Base class providing HTTP session with retry logic.

    By default uses ``cloudscraper`` to bypass Cloudflare-like protections.
    Subclasses that are blocked by cloudscraper's TLS fingerprint (e.g.
    Radware Bot Manager) can set ``USE_CLOUDSCRAPER = False`` to use a
    plain ``requests.Session`` instead.
    """

    USE_CLOUDSCRAPER: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.USE_CLOUDSCRAPER:
            self._session = cloudscraper.create_scraper()
        else:
            self._session = requests.Session()

    @abstractmethod
    def headers(self) -> dict[str, Any]:
        raise NotImplementedError

    def retry_request(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        max_retries: int = 3,
        backoff_factor: float = 2,
    ) -> requests.Response | None:
        if params is None:
            params = {}
        if headers is None:
            headers = self.headers()
        for i in range(max_retries + 1):
            try:
                response = self._session.get(
                    url, headers=headers, params=params, allow_redirects=True
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning("Connection error during attempt %d: %s", i + 1, e)
                if i < max_retries:
                    wait_time = (backoff_factor**i) * 1  # Exponential backoff
                    logger.debug("Retrying in %.2f seconds...", wait_time)
                    time.sleep(wait_time)
                else:
                    logger.error("Maximum number of retries reached for URL: %s", url)
                    return None
            except Exception as e:
                logger.error("Unexpected error during attempt %d: %s", i + 1, e)
                return None

        return None
