"""add notification_logs table

Revision ID: 003_notification_logs
Revises: 002_search_config_link
Create Date: 2026-04-10
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003_notification_logs"
down_revision = "002_search_config_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "price_alert_id",
            sa.Integer(),
            sa.ForeignKey("price_alerts.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id"),
            nullable=True,
        ),
        sa.Column("email_to", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), server_default="sent", nullable=False),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_notification_log_price_alert_id",
        "notification_logs",
        ["price_alert_id"],
    )
    op.create_index(
        "ix_notification_log_user_id",
        "notification_logs",
        ["user_id"],
    )
    op.create_index(
        "ix_notification_log_sent_at",
        "notification_logs",
        ["sent_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_log_sent_at", table_name="notification_logs")
    op.drop_index("ix_notification_log_user_id", table_name="notification_logs")
    op.drop_index(
        "ix_notification_log_price_alert_id", table_name="notification_logs"
    )
    op.drop_table("notification_logs")
