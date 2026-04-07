from abc import ABC, abstractmethod

from src.app.entities.price_history import PriceHistory as PriceHistoryEntity


class PriceHistoryRepositoryInterface(ABC):
    """Abstract interface for PriceHistory data access."""

    @abstractmethod
    def create(self, price_history: PriceHistoryEntity) -> PriceHistoryEntity:
        """Persist a new price record and return it with assigned id."""
        ...

    @abstractmethod
    def get_by_id(self, price_history_id: int) -> PriceHistoryEntity | None:
        """Retrieve a price record by its primary key."""
        ...

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> list[PriceHistoryEntity]:
        """Return all price records for a given product, ordered by created_at desc."""
        ...

    @abstractmethod
    def get_latest_by_product_id(self, product_id: int) -> PriceHistoryEntity | None:
        """Return the most recent price record for a given product."""
        ...

    @abstractmethod
    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[PriceHistoryEntity], int]:
        """Return a paginated list of all price records and the total count."""
        ...

    @abstractmethod
    def delete(self, price_history_id: int) -> bool:
        """Delete a price record by id. Returns True if deleted, False if not found."""
        ...
