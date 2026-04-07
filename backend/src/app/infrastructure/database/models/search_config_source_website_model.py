from sqlalchemy import Column, ForeignKey, Integer, Table

from src.app.infrastructure.database_config import Base

search_config_source_website = Table(
    "search_config_source_website",
    Base.metadata,
    Column(
        "search_config_id",
        Integer,
        ForeignKey("search_configs.id"),
        primary_key=True,
    ),
    Column(
        "source_website_id",
        Integer,
        ForeignKey("source_websites.id"),
        primary_key=True,
    ),
)
