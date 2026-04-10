from src.app.entities.price_alert import PriceAlert as PriceAlertEntity
from src.app.interfaces.repositories.price_alert_repository import (
    PriceAlertRepositoryInterface,
)


class CreatePriceAlertUseCase:
    """Create a new price alert for a user."""

    def __init__(self, price_alert_repo: PriceAlertRepositoryInterface):
        self.price_alert_repo = price_alert_repo

    def execute(self, price_alert: PriceAlertEntity) -> PriceAlertEntity:
        return self.price_alert_repo.create(price_alert)


class GetPriceAlertByIdUseCase:
    """Retrieve a single price alert by its id."""

    def __init__(self, price_alert_repo: PriceAlertRepositoryInterface):
        self.price_alert_repo = price_alert_repo

    def execute(self, price_alert_id: int) -> PriceAlertEntity | None:
        return self.price_alert_repo.get_by_id(price_alert_id)


class GetPriceAlertsByUserIdUseCase:
    """Retrieve all price alerts for a given user."""

    def __init__(self, price_alert_repo: PriceAlertRepositoryInterface):
        self.price_alert_repo = price_alert_repo

    def execute(self, user_id: int) -> list[PriceAlertEntity]:
        return self.price_alert_repo.get_by_user_id(user_id)


class ListPriceAlertsUseCase:
    """List all price alerts with pagination and sorting."""

    def __init__(self, price_alert_repo: PriceAlertRepositoryInterface):
        self.price_alert_repo = price_alert_repo

    def execute(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[PriceAlertEntity], int]:
        return self.price_alert_repo.get_all(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )


class UpdatePriceAlertUseCase:
    """Update an existing price alert."""

    def __init__(self, price_alert_repo: PriceAlertRepositoryInterface):
        self.price_alert_repo = price_alert_repo

    def execute(
        self, price_alert_id: int, price_alert: PriceAlertEntity
    ) -> PriceAlertEntity | None:
        return self.price_alert_repo.update(price_alert_id, price_alert)


class DeletePriceAlertUseCase:
    """Delete a price alert by id."""

    def __init__(self, price_alert_repo: PriceAlertRepositoryInterface):
        self.price_alert_repo = price_alert_repo

    def execute(self, price_alert_id: int) -> bool:
        return self.price_alert_repo.delete(price_alert_id)
