from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceWebsite(BaseModel):
    """Source website domain entity representing e-commerce platforms."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    base_url: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
