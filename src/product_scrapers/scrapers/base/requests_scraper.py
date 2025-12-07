import cloudscraper
import requests
import time
from abc import ABC, abstractmethod

from typing import Optional, Dict, Any


class RequestScraper(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = cloudscraper.create_scraper()

    @abstractmethod
    def headers(self) -> Dict[str, Any]:
        raise NotImplementedError

    def retry_request(
        self,
        url: str,
        headers: dict = {},
        params: dict = {},
        max_retries: int = 3,
        backoff_factor: float = 2,
    ) -> Optional[requests.Response]:
        for i in range(max_retries + 1):
            try:
                response = self._session.get(
                    url, headers=headers, params=params, allow_redirects=True
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"Connection error during attempt {i + 1}: {str(e)}")
                if i < max_retries:
                    wait_time = (backoff_factor**i) * 1  # Exponential backoff
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Maximum number of retries reached.")
                    return None
            except Exception as e:
                print(f"unexpected error during attempt {i + 1}: {str(e)}")
                return None

        return None
