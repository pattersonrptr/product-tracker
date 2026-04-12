"""Plan limits enforcement.

Provides a FastAPI dependency that loads the current user's plan limits
and helper functions to validate operations against those limits.
"""

from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from src.app.entities.user import User as UserEntity
from src.app.infrastructure.database.models.plan_model import Plan as PlanModel
from src.app.infrastructure.database.models.price_alert_model import (
    PriceAlert as PriceAlertModel,
)
from src.app.infrastructure.database.models.subscription_model import (
    Subscription as SubscriptionModel,
)
from src.app.infrastructure.database_config import get_db
from src.app.security.auth import get_current_active_user
from src.common.jsonapi import JsonApiError

# Default limits for users without a subscription (free tier)
FREE_PLAN_DEFAULTS = {
    "max_active_alerts": 3,
    "min_frequency_minutes": 360,
    "price_history_days": 7,
    "max_sources": 2,
}


@dataclass
class PlanLimits:
    plan_name: str
    max_active_alerts: int | None  # None = unlimited
    min_frequency_minutes: int
    price_history_days: int | None  # None = unlimited
    max_sources: int | None  # None = all


def get_user_plan_limits(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_active_user),
) -> PlanLimits:
    """FastAPI dependency that returns the current user's plan limits."""
    sub = (
        db.query(SubscriptionModel)
        .filter(
            SubscriptionModel.user_id == current_user.id,
            SubscriptionModel.status == "active",
        )
        .first()
    )

    if sub:
        plan = db.query(PlanModel).filter(PlanModel.id == sub.plan_id).first()
        if plan:
            return PlanLimits(
                plan_name=plan.name,
                max_active_alerts=plan.max_active_alerts,
                min_frequency_minutes=plan.min_frequency_minutes,
                price_history_days=plan.price_history_days,
                max_sources=plan.max_sources,
            )

    # No subscription or plan not found → free defaults
    return PlanLimits(
        plan_name="free",
        max_active_alerts=FREE_PLAN_DEFAULTS["max_active_alerts"],
        min_frequency_minutes=FREE_PLAN_DEFAULTS["min_frequency_minutes"],
        price_history_days=FREE_PLAN_DEFAULTS["price_history_days"],
        max_sources=FREE_PLAN_DEFAULTS["max_sources"],
    )


def check_alert_limit(
    db: Session, user_id: int, limits: PlanLimits
) -> JsonApiError | None:
    """Check if user can create a new active alert."""
    if limits.max_active_alerts is None:
        return None  # unlimited

    active_count = (
        db.query(PriceAlertModel)
        .filter(
            PriceAlertModel.user_id == user_id,
            PriceAlertModel.is_active.is_(True),
            PriceAlertModel.deleted_at.is_(None),
        )
        .count()
    )

    if active_count >= limits.max_active_alerts:
        return JsonApiError(
            status="403",
            code="PLAN_LIMIT_REACHED",
            title="Alert limit reached",
            detail=(
                f"Your {limits.plan_name} plan allows up to "
                f"{limits.max_active_alerts} active alerts. "
                f"Upgrade your plan for more."
            ),
            source={"pointer": "/data/attributes/is_active"},
        )
    return None


def check_frequency_limit(
    frequency_minutes: int, limits: PlanLimits
) -> JsonApiError | None:
    """Check if the requested frequency is allowed by the user's plan."""
    if frequency_minutes < limits.min_frequency_minutes:
        return JsonApiError(
            status="403",
            code="PLAN_LIMIT_REACHED",
            title="Frequency too high for your plan",
            detail=(
                f"Your {limits.plan_name} plan allows minimum frequency of "
                f"{limits.min_frequency_minutes} minutes. "
                f"Upgrade your plan for faster checks."
            ),
            source={"pointer": "/data/attributes/frequency_minutes"},
        )
    return None


def check_source_limit(source_count: int, limits: PlanLimits) -> JsonApiError | None:
    """Check if the number of sources is allowed by the user's plan."""
    if limits.max_sources is None:
        return None  # unlimited

    if source_count > limits.max_sources:
        return JsonApiError(
            status="403",
            code="PLAN_LIMIT_REACHED",
            title="Source limit reached",
            detail=(
                f"Your {limits.plan_name} plan allows up to "
                f"{limits.max_sources} sources per alert. "
                f"Upgrade your plan for more."
            ),
            source={"pointer": "/data/attributes/source_website_ids"},
        )
    return None
