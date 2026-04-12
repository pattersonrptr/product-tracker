from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from src.app.infrastructure.database_config import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # "free", "pro", "business"
    display_name = Column(String(100), nullable=False)
    price_cents = Column(Integer, nullable=False, default=0)
    max_active_alerts = Column(Integer, nullable=True)  # NULL = unlimited
    min_frequency_minutes = Column(Integer, nullable=False, default=360)
    price_history_days = Column(Integer, nullable=True, default=7)  # NULL = unlimited
    max_sources = Column(Integer, nullable=True)  # NULL = all
    has_push_notifications = Column(Boolean, default=False)
    has_whatsapp_notifications = Column(Boolean, default=False)
    has_api_access = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
