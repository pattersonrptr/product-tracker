from abc import ABC, abstractmethod
from datetime import datetime

from src.app.entities.notification_log import NotificationLog as NotificationLogEntity


class NotificationLogRepositoryInterface(ABC):
    """Abstract interface for NotificationLog data access."""

    @abstractmethod
    def create(self, notification_log: NotificationLogEntity) -> NotificationLogEntity:
        """Persist a new notification log and return it with assigned id."""
        ...

    @abstractmethod
    def get_by_id(self, notification_log_id: int) -> NotificationLogEntity | None:
        """Retrieve a notification log by its primary key."""
        ...

    @abstractmethod
    def get_by_price_alert_id(self, price_alert_id: int) -> list[NotificationLogEntity]:
        """Return all logs for a given price alert, ordered by sent_at desc."""
        ...

    @abstractmethod
    def get_last_sent_for_alert(
        self, price_alert_id: int
    ) -> NotificationLogEntity | None:
        """Return the most recent successfully sent notification for a price alert."""
        ...

    @abstractmethod
    def count_since(self, price_alert_id: int, since: datetime) -> int:
        """Count successfully sent notifications for a price alert since a given time."""
        ...

    @abstractmethod
    def exists_for_product_and_alert(
        self, product_id: int, price_alert_id: int
    ) -> bool:
        """Return True if a successful notification was already sent for this exact product+alert pair."""
        ...

    @abstractmethod
    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[NotificationLogEntity], int]:
        """Return a paginated list of all notification logs and the total count."""
        ...

    @abstractmethod
    def delete(self, notification_log_id: int) -> bool:
        """Delete a log by id. Returns True if deleted, False if not found."""
        ...
