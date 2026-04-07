from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class PriceHistory(BaseModel):
    """PriceHistory domain entity representing a price record for a tracked product."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    product_id: int
    price: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
