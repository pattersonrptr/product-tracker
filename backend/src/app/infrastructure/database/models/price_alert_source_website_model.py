from sqlalchemy import Column, ForeignKey, Integer, Table

from src.app.infrastructure.database_config import Base

price_alert_source_website = Table(
    "price_alert_source_website",
    Base.metadata,
    Column(
        "price_alert_id",
        Integer,
        ForeignKey("price_alerts.id"),
        primary_key=True,
    ),
    Column(
        "source_website_id",
        Integer,
        ForeignKey("source_websites.id"),
        primary_key=True,
    ),
)
