from src.app.entities.price_history import PriceHistory as PriceHistoryEntity
from src.app.interfaces.repositories.price_history_repository import (
    PriceHistoryRepositoryInterface,
)


class CreatePriceHistoryUseCase:
    """Record a new price entry for a product."""

    def __init__(self, price_history_repo: PriceHistoryRepositoryInterface):
        self.price_history_repo = price_history_repo

    def execute(self, price_history: PriceHistoryEntity) -> PriceHistoryEntity:
        return self.price_history_repo.create(price_history)


class GetPriceHistoryByIdUseCase:
    """Retrieve a single price record by its id."""

    def __init__(self, price_history_repo: PriceHistoryRepositoryInterface):
        self.price_history_repo = price_history_repo

    def execute(self, price_history_id: int) -> PriceHistoryEntity | None:
        return self.price_history_repo.get_by_id(price_history_id)


class GetPriceHistoryByProductIdUseCase:
    """Retrieve all price records for a given product."""

    def __init__(self, price_history_repo: PriceHistoryRepositoryInterface):
        self.price_history_repo = price_history_repo

    def execute(self, product_id: int) -> list[PriceHistoryEntity]:
        return self.price_history_repo.get_by_product_id(product_id)


class GetLatestPriceByProductIdUseCase:
    """Retrieve the most recent price record for a given product."""

    def __init__(self, price_history_repo: PriceHistoryRepositoryInterface):
        self.price_history_repo = price_history_repo

    def execute(self, product_id: int) -> PriceHistoryEntity | None:
        return self.price_history_repo.get_latest_by_product_id(product_id)


class ListPriceHistoriesUseCase:
    """List all price records with pagination and sorting."""

    def __init__(self, price_history_repo: PriceHistoryRepositoryInterface):
        self.price_history_repo = price_history_repo

    def execute(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[PriceHistoryEntity], int]:
        return self.price_history_repo.get_all(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )


class DeletePriceHistoryUseCase:
    """Delete a price record by id."""

    def __init__(self, price_history_repo: PriceHistoryRepositoryInterface):
        self.price_history_repo = price_history_repo

    def execute(self, price_history_id: int) -> bool:
        return self.price_history_repo.delete(price_history_id)
