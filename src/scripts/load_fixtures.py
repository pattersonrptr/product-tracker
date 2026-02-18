import argparse

from src.app.fixtures.fixtures import get_fixtures

# from src.app.infrastructure.database.models.source_website_model import SourceWebsite
# from src.app.infrastructure.database.models.product_model import Product
# from src.app.infrastructure.database.models.price_history_model import PriceHistory
from src.app.infrastructure.database.models.user_model import User
from src.app.infrastructure.database_config import SessionLocal

# from src.app.infrastructure.database.models.search_config_model import SearchConfig
# from src.app.infrastructure.database.models.search_config_source_website_model import (
#     search_config_source_website,
# )

FIXTURE_DEPENDENCIES = {
    "all": ["source_websites", "users", "products", "price_history", "search_configs"],
    "users": [],
    "source_websites": [],
    "products": ["source_websites"],
    "price_history": ["products"],
    "search_configs": ["users", "source_websites"],
}

FIXTURE_INSERT_ORDER = [
    "source_websites",
    "users",
    "products",
    "price_history",
    "search_configs",
]


def resolve_dependencies(selected):
    resolved = set()

    def add_with_deps(fixture):
        if fixture not in resolved:
            for dep in FIXTURE_DEPENDENCIES.get(fixture, []):
                add_with_deps(dep)
            resolved.add(fixture)

    for f in selected:
        add_with_deps(f)
    # Returns the fixtures in the order they should be inserted
    return [f for f in FIXTURE_INSERT_ORDER if f in resolved]


def load_fixtures(selected_fixtures):
    db = SessionLocal()
    data = get_fixtures()
    try:
        if "source_websites" in selected_fixtures:
            db.bulk_insert_mappings(SourceWebsite, data["source_websites"])

        if "users" in selected_fixtures:
            db.bulk_insert_mappings(User, data.get("users", []))

        if "products" in selected_fixtures:
            db.bulk_insert_mappings(Product, data["products"])

        if "price_history" in selected_fixtures:
            db.bulk_insert_mappings(PriceHistory, data["price_history"])

        if "search_configs" in selected_fixtures:
            search_configs_data = []
            for sc in data["search_configs"]:
                sc_copy = sc.copy()
                sc_copy.pop("source_website_ids", None)
                search_configs_data.append(sc_copy)
            db.bulk_insert_mappings(SearchConfig, search_configs_data)
            search_config_source_website_data = []
            for sc in data["search_configs"]:
                search_config_id = sc["id"]
                source_website_ids = sc.get("source_website_ids", [])
                for sw_id in source_website_ids:
                    search_config_source_website_data.append(
                        {
                            "search_config_id": search_config_id,
                            "source_website_id": sw_id,
                        }
                    )
            for data_point in search_config_source_website_data:
                stmt = search_config_source_website.insert().values(data_point)
                db.execute(stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load fixtures into the database.")
    parser.add_argument(
        "fixtures",
        nargs="+",
        choices=list(FIXTURE_DEPENDENCIES.keys()),
        help="Fixtures to be loaded (ex: users, source_websites, price_history, products, search_configs)",
    )
    args = parser.parse_args()
    fixtures_to_load = resolve_dependencies(args.fixtures)
    print(f"Loading fixtures: {fixtures_to_load}")
    load_fixtures(fixtures_to_load)
    print("Fixtures loaded successfully.")
