from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class Subscription(BaseModel):
    """Subscription domain entity linking a user to a plan."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    plan_id: int
    status: str = "active"  # "active", "canceled", "past_due"
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(UTC))
    current_period_end: datetime | None = None  # None = no expiry (free plan)
    canceled_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
