from datetime import datetime

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.app.entities.notification_log import NotificationLog as NotificationLogEntity
from src.app.infrastructure.database.models.notification_log_model import (
    NotificationLog as NotificationLogModel,
)
from src.app.interfaces.repositories.notification_log_repository import (
    NotificationLogRepositoryInterface,
)


class NotificationLogRepository(NotificationLogRepositoryInterface):
    """SQLAlchemy implementation of NotificationLogRepositoryInterface."""

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: NotificationLogModel) -> NotificationLogEntity:
        return NotificationLogEntity(
            id=model.id,
            price_alert_id=model.price_alert_id,
            user_id=model.user_id,
            product_id=model.product_id,
            email_to=model.email_to,
            subject=model.subject,
            status=model.status,
            error_message=model.error_message,
            sent_at=model.sent_at,
            created_at=model.created_at,
        )

    def create(self, notification_log: NotificationLogEntity) -> NotificationLogEntity:
        """Persist a new notification log."""
        db_log = NotificationLogModel(
            price_alert_id=notification_log.price_alert_id,
            user_id=notification_log.user_id,
            product_id=notification_log.product_id,
            email_to=notification_log.email_to,
            subject=notification_log.subject,
            status=notification_log.status,
            error_message=notification_log.error_message,
            sent_at=notification_log.sent_at,
            created_at=notification_log.created_at,
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return self._to_entity(db_log)

    def get_by_id(self, notification_log_id: int) -> NotificationLogEntity | None:
        """Retrieve a notification log by its primary key."""
        db_log = (
            self.db.query(NotificationLogModel)
            .filter(NotificationLogModel.id == notification_log_id)
            .first()
        )
        return self._to_entity(db_log) if db_log else None

    def get_by_price_alert_id(self, price_alert_id: int) -> list[NotificationLogEntity]:
        """Return all logs for a given price alert, ordered by sent_at desc."""
        records = (
            self.db.query(NotificationLogModel)
            .filter(NotificationLogModel.price_alert_id == price_alert_id)
            .order_by(desc(NotificationLogModel.sent_at))
            .all()
        )
        return [self._to_entity(r) for r in records]

    def get_last_sent_for_alert(
        self, price_alert_id: int
    ) -> NotificationLogEntity | None:
        """Return the most recent successfully sent notification for a price alert."""
        db_log = (
            self.db.query(NotificationLogModel)
            .filter(
                NotificationLogModel.price_alert_id == price_alert_id,
                NotificationLogModel.status == "sent",
            )
            .order_by(desc(NotificationLogModel.sent_at))
            .first()
        )
        return self._to_entity(db_log) if db_log else None

    def count_since(self, price_alert_id: int, since: datetime) -> int:
        """Count successfully sent notifications for a price alert since a given time."""
        return (
            self.db.query(NotificationLogModel)
            .filter(
                NotificationLogModel.price_alert_id == price_alert_id,
                NotificationLogModel.status == "sent",
                NotificationLogModel.sent_at >= since,
            )
            .count()
        )

    def exists_for_product_and_alert(
        self, product_id: int, price_alert_id: int
    ) -> bool:
        """Return True if a successful notification was already sent for this exact product+alert pair."""
        return (
            self.db.query(NotificationLogModel)
            .filter(
                NotificationLogModel.product_id == product_id,
                NotificationLogModel.price_alert_id == price_alert_id,
                NotificationLogModel.status == "sent",
            )
            .first()
            is not None
        )

    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[NotificationLogEntity], int]:
        """Return a paginated list of all notification logs and the total count."""
        query = self.db.query(NotificationLogModel)

        total = query.count()

        if sort_by and hasattr(NotificationLogModel, sort_by):
            order_column = getattr(NotificationLogModel, sort_by)
            query = query.order_by(
                desc(order_column) if sort_order == "desc" else asc(order_column)
            )
        else:
            query = query.order_by(desc(NotificationLogModel.sent_at))

        records = query.limit(limit).offset(offset).all()
        return [self._to_entity(r) for r in records], total

    def delete(self, notification_log_id: int) -> bool:
        """Delete a notification log by id."""
        db_log = (
            self.db.query(NotificationLogModel)
            .filter(NotificationLogModel.id == notification_log_id)
            .first()
        )
        if not db_log:
            return False
        self.db.delete(db_log)
        self.db.commit()
        return True
