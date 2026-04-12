from pydantic import BaseModel, ConfigDict


class Plan(BaseModel):
    """Plan domain entity representing a subscription tier."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str  # "free", "pro", "business"
    display_name: str  # "Free", "Pro", "Business"
    price_cents: int = 0  # price in BRL cents (e.g. 2900 = R$29)
    max_active_alerts: int | None = None  # None = unlimited
    min_frequency_minutes: int = 360  # minimum check interval
    price_history_days: int | None = 7  # None = unlimited
    max_sources: int | None = None  # None = all
    has_push_notifications: bool = False
    has_whatsapp_notifications: bool = False
    has_api_access: bool = False
    is_active: bool = True
