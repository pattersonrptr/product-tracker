"""add price_alerts and price_alert_source_website tables

Revision ID: 001_price_alerts
Revises:
Create Date: 2025-04-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_price_alerts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("search_term", sa.String(255), nullable=False),
        sa.Column("max_price", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "frequency_minutes", sa.Integer(), nullable=False, server_default="60"
        ),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_price_alert_term", "price_alerts", ["search_term"])
    op.create_index("ix_price_alert_active", "price_alerts", ["is_active"])
    op.create_index("ix_price_alert_user_id", "price_alerts", ["user_id"])

    op.create_table(
        "price_alert_source_website",
        sa.Column(
            "price_alert_id",
            sa.Integer(),
            sa.ForeignKey("price_alerts.id"),
            primary_key=True,
        ),
        sa.Column(
            "source_website_id",
            sa.Integer(),
            sa.ForeignKey("source_websites.id"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("price_alert_source_website")
    op.drop_index("ix_price_alert_user_id", table_name="price_alerts")
    op.drop_index("ix_price_alert_active", table_name="price_alerts")
    op.drop_index("ix_price_alert_term", table_name="price_alerts")
    op.drop_table("price_alerts")
