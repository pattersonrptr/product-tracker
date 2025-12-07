import os
from typing import List, Dict, Any

import requests


class ApiClient:
    def __init__(self, access_token=None):
        self.base_url = os.getenv("API_URL", "web:8000")
        self.access_token = access_token
        self.headers = {}

        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    def _make_request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        print("data: ", data)
        try:
            response = requests.request(
                method, url, headers=self.headers, json=data, params=params, timeout=10
            )
            response.raise_for_status()
            return response
        except Exception as e:  # Alterado para capturar qualquer exceção
            print(f"🔴 Request error at {url}: {e}")
            return requests.Response()

    def get_search_configs_by_id(self, search_config_id: int) -> Dict[str, Any]:
        print(f"🔎 Getting search config by ID: {search_config_id}")
        response = self._make_request("GET", f"/search_configs/{search_config_id}/")
        if response.status_code == 200 and response.json():
            return response.json()
        print(f"🔴 Search config with ID {search_config_id} not found.")
        return {}

    def get_search_configs_by_source_website(self, source_website_name: str):
        print(f"🔎 Getting search configs for source website: {source_website_name}")
        source_website = self.get_source_website_by_name(source_website_name)
        source_website_id = source_website.get("id")
        if not source_website_id:
            print(f"🔴 Source website '{source_website_name}' not found.")
            return []
        response = self._make_request(
            "GET", f"/search_configs/source_websites/{source_website_id}/"
        )
        return (
            response.json() if response.status_code == 200 and response.json() else []
        )

    def get_active_searches(self) -> List[Dict[str, Any]]:
        print("🔎 Getting search configs")
        response = self._make_request("GET", "/search_configs/")
        return [item for item in response.json() if item.get("is_active")]

    def get_source_website_by_name(self, website_name: str) -> Dict[str, Any]:
        print(f"🔎 Checking if source website {website_name} exists")
        response = self._make_request("GET", f"/source_websites/name/{website_name}")
        return (
            response.json() if response.status_code == 200 and response.json() else {}
        )

    def get_existing_product_urls(self, scraper_name):
        print("🔎 Checking existing products")
        response = self._make_request("GET", "/products/")
        existing_products = response.json() if response.status_code == 200 else []
        return {p["url"] for p in existing_products if scraper_name in ["url"]}

    def create_product(self, product):
        print(f"💾 Creating product: {product['url']}")
        response = self._make_request("POST", "/products/", data=product)
        return response.status_code == 201

    def product_exists(self, product) -> bool:
        print("🔎 Checking if product exists")
        response = self._make_request("GET", f"/products/url/{product['url']}")
        if response.status_code == 200 and response.json():
            print(response.status_code)
            print(response.json())
            return True
        return False

    def create_new_products(self, products: list[dict]) -> int:
        print(f"💾 Saving {len(products)} products")
        created = 0
        for product in products:
            if not self.product_exists(product):
                if self.create_product(product):
                    created += 1
        print(f"✅ {created} new products created")
        return created

    def get_products(self, params=None):
        print("🔄 Updating products by URLs")
        response = self._make_request("GET", "/products/filter/", params=params)
        return (
            response.json() if response.status_code == 200 and response.json() else []
        )

    def update_product_list(self, products):
        print(f"💾 Updating {len(products)} products")
        updated = 0
        for product in products:
            print(80 * "-")
            print(product)
            print(80 * "-")
            response = self._make_request(
                "PUT", f"/products/{product['id']}", data=product
            )
            if response.status_code == 200:
                updated += 1
        print(f"✅ {updated} products updated")
        return updated
