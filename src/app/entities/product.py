from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProductCondition(str, Enum):
    """Product condition enumeration."""

    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    UNDETERMINED = "undetermined"


class Product(BaseModel):
    """Product domain entity representing a tracked product from e-commerce sites."""

    # Identification
    id: int | None = None
    url: str
    title: str
    source_product_code: str | None = None

    # Content
    description: str | None = None
    image_urls: str | None = None  # URLs separated by commas

    # Location
    city: str | None = None
    state: str | None = None

    # Product details
    condition: ProductCondition = ProductCondition.UNDETERMINED
    seller_name: str | None = None
    is_available: bool = True

    # Source information
    source_website_id: int
    source_metadata: dict | None = None

    # Current price (calculated from price_history)
    current_price: float | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        use_enum_values = True
