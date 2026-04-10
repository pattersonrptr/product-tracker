"""add search_config_id FK to price_alerts

Revision ID: 002_search_config_link
Revises: 001_price_alerts
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_search_config_link"
down_revision = "001_price_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "price_alerts",
        sa.Column(
            "search_config_id",
            sa.Integer(),
            sa.ForeignKey("search_configs.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_price_alert_search_config_id",
        "price_alerts",
        ["search_config_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_price_alert_search_config_id", table_name="price_alerts")
    op.drop_column("price_alerts", "search_config_id")
