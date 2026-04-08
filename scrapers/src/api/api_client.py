import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ApiClient:
    """HTTP client for communicating with the product-tracker JSON:API."""

    def __init__(self, access_token=None):
        self.base_url = os.getenv("API_URL", "http://web:8000")
        self.access_token = access_token
        self.headers = {"Content-Type": "application/vnd.api+json"}

        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _make_request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method, url, headers=self.headers, json=data, params=params, timeout=10
            )
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error("Request error at %s: %s", url, e)
            return requests.Response()

    @staticmethod
    def _extract_attributes(resource: dict) -> dict[str, Any]:
        """Extract a flat dict from a JSON:API resource object.

        Returns ``{"id": ..., **attributes}`` so callers can use simple key
        access (e.g. ``item["name"]``, ``item["id"]``).
        """
        if not resource or "data" not in resource:
            return {}
        data = resource["data"]
        if not data:
            return {}
        attrs = data.get("attributes", {})
        return {"id": data.get("id"), **attrs}

    @staticmethod
    def _extract_collection(response_json: dict) -> list[dict[str, Any]]:
        """Extract a list of flat dicts from a JSON:API collection response."""
        if not response_json or "data" not in response_json:
            return []
        return [
            {"id": item.get("id"), **item.get("attributes", {})}
            for item in response_json["data"]
        ]

    @staticmethod
    def _wrap_for_creation(type_name: str, attributes: dict) -> dict:
        """Wrap attributes in a JSON:API creation request envelope."""
        return {"data": {"type": type_name, "attributes": attributes}}

    @staticmethod
    def _wrap_for_update(
        type_name: str, resource_id: str | int, attributes: dict
    ) -> dict:
        """Wrap attributes in a JSON:API update request envelope."""
        return {
            "data": {
                "type": type_name,
                "id": str(resource_id),
                "attributes": attributes,
            }
        }

    # -------------------------------------------------------------------------
    # Search configs
    # -------------------------------------------------------------------------

    def get_search_config_by_id(self, search_config_id: int) -> dict[str, Any]:
        logger.debug("Getting search config by ID: %s", search_config_id)
        response = self._make_request("GET", f"/search-configs/{search_config_id}")
        if response.status_code == 200:
            return self._extract_attributes(response.json())
        logger.warning("Search config with ID %s not found.", search_config_id)
        return {}

    def get_active_search_configs(self) -> list[dict[str, Any]]:
        logger.debug("Getting active search configs")
        response = self._make_request(
            "GET", "/search-configs/", params={"is_active": True}
        )
        if response.status_code == 200:
            return self._extract_collection(response.json())
        return []

    # -------------------------------------------------------------------------
    # Source websites
    # -------------------------------------------------------------------------

    def get_source_website_by_name(self, website_name: str) -> dict[str, Any]:
        logger.debug("Getting source website by name: %s", website_name)
        response = self._make_request("GET", f"/source-websites/name/{website_name}")
        if response.status_code == 200:
            return self._extract_attributes(response.json())
        logger.warning("Source website '%s' not found.", website_name)
        return {}

    # -------------------------------------------------------------------------
    # Products
    # -------------------------------------------------------------------------

    def get_products(self, params: dict = None) -> list[dict[str, Any]]:
        logger.debug("Getting products with params: %s", params)
        response = self._make_request("GET", "/products/", params=params)
        if response.status_code == 200:
            return self._extract_collection(response.json())
        return []

    def get_product_by_url(self, url: str) -> dict[str, Any]:
        logger.debug("Getting product by URL: %s", url)
        response = self._make_request("GET", "/products/url", params={"url": url})
        if response.status_code == 200:
            return self._extract_attributes(response.json())
        return {}

    def product_exists(self, url: str) -> bool:
        logger.debug("Checking if product exists: %s", url)
        return bool(self.get_product_by_url(url))

    def create_product(self, product: dict) -> dict[str, Any]:
        logger.debug("Creating product: %s", product.get("url"))
        payload = self._wrap_for_creation("product", product)
        response = self._make_request("POST", "/products/", data=payload)
        if response.status_code == 201:
            return self._extract_attributes(response.json())
        return {}

    def update_product(self, product_id: int | str, product: dict) -> dict[str, Any]:
        logger.debug("Updating product ID: %s", product_id)
        payload = self._wrap_for_update("product", product_id, product)
        response = self._make_request("PUT", f"/products/{product_id}", data=payload)
        if response.status_code == 200:
            return self._extract_attributes(response.json())
        return {}

    def create_new_products(self, products: list[dict]) -> int:
        """Create products that don't already exist. Returns number created."""
        logger.debug("Saving %d products", len(products))
        created = 0
        for product in products:
            if not self.product_exists(product["url"]):
                result = self.create_product(product)
                if result:
                    created += 1
        logger.info("%d new products created", created)
        return created

    def update_product_list(self, products: list[dict]) -> int:
        """Update a list of products. Returns number successfully updated."""
        logger.debug("Updating %d products", len(products))
        updated = 0
        for product in products:
            result = self.update_product(product["id"], product)
            if result:
                updated += 1
        logger.info("%d products updated", updated)
        return updated

    def get_existing_product_urls(self, source_website_name: str) -> set[str]:
        """Return the set of URLs already tracked for a given source website."""
        logger.debug("Getting existing product URLs for: %s", source_website_name)
        source_website = self.get_source_website_by_name(source_website_name)
        source_website_id = source_website.get("id")
        if not source_website_id:
            return set()
        products = self.get_products(params={"source_website_id": source_website_id})
        return {p["url"] for p in products if p.get("url")}

    # -------------------------------------------------------------------------
    # Price histories
    # -------------------------------------------------------------------------

    def create_price_history(
        self, product_id: int | str, price: float
    ) -> dict[str, Any]:
        logger.debug("Creating price history for product ID %s: %s", product_id, price)
        payload = self._wrap_for_creation(
            "price_history", {"product_id": int(product_id), "price": price}
        )
        response = self._make_request("POST", "/price-histories/", data=payload)
        if response.status_code == 201:
            return self._extract_attributes(response.json())
        logger.error("Failed to create price history for product %s", product_id)
        return {}

    # -------------------------------------------------------------------------
    # Search execution logs
    # -------------------------------------------------------------------------

    def create_search_execution_log(
        self,
        search_config_id: int,
        status: str,
        results_count: int = 0,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        logger.debug("Creating search execution log for config ID %s", search_config_id)
        attributes: dict[str, Any] = {
            "search_config_id": search_config_id,
            "status": status,
            "results_count": results_count,
        }
        if error_message:
            attributes["error_message"] = error_message
        payload = self._wrap_for_creation("search_execution_log", attributes)
        response = self._make_request("POST", "/search-execution-logs/", data=payload)
        if response.status_code == 201:
            return self._extract_attributes(response.json())
        logger.error(
            "Failed to create search execution log for config %s", search_config_id
        )
        return {}
