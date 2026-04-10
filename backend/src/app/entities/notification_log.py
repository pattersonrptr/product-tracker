from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationStatus = Literal["sent", "failed"]


class NotificationLog(BaseModel):
    """NotificationLog domain entity representing a sent email notification."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    price_alert_id: int
    user_id: int
    product_id: int | None = None
    email_to: str
    subject: str
    status: NotificationStatus = "sent"
    error_message: str | None = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
