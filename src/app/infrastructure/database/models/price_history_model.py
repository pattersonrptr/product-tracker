from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import relationship

from src.app.infrastructure.database_config import Base


class PriceHistory(Base):
    """PriceHistory SQLAlchemy model — append-only price records per product."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the tracked product",
    )
    price = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Recorded price at this point in time",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index("ix_price_history_product_created", "product_id", "created_at"),
    )
