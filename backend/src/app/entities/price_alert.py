from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class PriceAlert(BaseModel):
    """PriceAlert domain entity representing a user's price monitoring alert."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    search_term: str
    max_price: float
    is_active: bool = True
    frequency_minutes: int = 60
    last_triggered_at: datetime | None = None
    user_id: int | None = None
    search_config_id: int | None = None
    source_website_ids: list[int] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None
