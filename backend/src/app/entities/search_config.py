from datetime import UTC, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class SearchConfig(BaseModel):
    """SearchConfig domain entity representing a user's product search configuration."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    search_term: str
    is_active: bool = True
    frequency_days: int = 1
    preferred_time: time = time(0, 0)
    search_metadata: dict | None = None
    user_id: int | None = None
    source_website_ids: list[int] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
