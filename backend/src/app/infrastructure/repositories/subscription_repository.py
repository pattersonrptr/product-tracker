from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from src.app.entities.subscription import Subscription as SubscriptionEntity
from src.app.infrastructure.database.models.subscription_model import (
    Subscription as SubscriptionModel,
)
from src.app.interfaces.repositories.subscription_repository import (
    SubscriptionRepositoryInterface,
)


class SubscriptionRepository(SubscriptionRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def create(self, subscription: SubscriptionEntity) -> SubscriptionEntity:
        db_sub = SubscriptionModel(**subscription.model_dump(exclude={"id"}))
        self.db.add(db_sub)
        self.db.commit()
        self.db.refresh(db_sub)
        return SubscriptionEntity.model_validate(db_sub)

    def get_by_id(self, subscription_id: int) -> SubscriptionEntity | None:
        sub = (
            self.db.query(SubscriptionModel)
            .options(joinedload(SubscriptionModel.plan))
            .filter(SubscriptionModel.id == subscription_id)
            .first()
        )
        if sub:
            return SubscriptionEntity.model_validate(sub)
        return None

    def get_by_user_id(self, user_id: int) -> SubscriptionEntity | None:
        sub = (
            self.db.query(SubscriptionModel)
            .options(joinedload(SubscriptionModel.plan))
            .filter(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == "active",
            )
            .first()
        )
        if sub:
            return SubscriptionEntity.model_validate(sub)
        return None

    def update(
        self, subscription_id: int, subscription: SubscriptionEntity
    ) -> SubscriptionEntity | None:
        db_sub = (
            self.db.query(SubscriptionModel)
            .filter(SubscriptionModel.id == subscription_id)
            .first()
        )
        if not db_sub:
            return None
        for key, value in subscription.model_dump(
            exclude_unset=True, exclude={"id"}
        ).items():
            setattr(db_sub, key, value)
        db_sub.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(db_sub)
        return SubscriptionEntity.model_validate(db_sub)
