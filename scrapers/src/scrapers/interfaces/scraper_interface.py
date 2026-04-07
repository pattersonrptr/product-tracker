from abc import ABC, abstractmethod
from typing import Any


class ScraperInterface(ABC):
    @abstractmethod
    def search(self, search_term: str) -> list:
        """
        Search for a product using the given search term.
        Returns the HTML content of the search results page.
        """
        raise NotImplementedError

    @abstractmethod
    def scrape_data(self, url: str) -> dict[str, Any]:
        """
        Scrape data from the given product URL.
        """
        raise NotImplementedError

    @abstractmethod
    def update_data(self, product: dict[str, Any]) -> dict[str, Any]:
        """
        Update the product data with the latest information from the URL.
        """
        raise NotImplementedError
