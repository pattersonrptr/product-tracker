from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.app.entities.price_history import PriceHistory as PriceHistoryEntity
from src.app.infrastructure.database.models.price_history_model import (
    PriceHistory as PriceHistoryModel,
)
from src.app.interfaces.repositories.price_history_repository import (
    PriceHistoryRepositoryInterface,
)


class PriceHistoryRepository(PriceHistoryRepositoryInterface):
    """SQLAlchemy implementation of PriceHistoryRepositoryInterface."""

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: PriceHistoryModel) -> PriceHistoryEntity:
        return PriceHistoryEntity(
            id=model.id,
            product_id=model.product_id,
            price=float(model.price),
            created_at=model.created_at,
        )

    def create(self, price_history: PriceHistoryEntity) -> PriceHistoryEntity:
        """Persist a new price record."""
        db_price_history = PriceHistoryModel(
            product_id=price_history.product_id,
            price=price_history.price,
        )
        self.db.add(db_price_history)
        self.db.commit()
        self.db.refresh(db_price_history)
        return self._to_entity(db_price_history)

    def get_by_id(self, price_history_id: int) -> PriceHistoryEntity | None:
        """Retrieve a price record by its primary key."""
        db_record = (
            self.db.query(PriceHistoryModel)
            .filter(PriceHistoryModel.id == price_history_id)
            .first()
        )
        return self._to_entity(db_record) if db_record else None

    def get_by_product_id(self, product_id: int) -> list[PriceHistoryEntity]:
        """Return all price records for a product, ordered by created_at desc."""
        records = (
            self.db.query(PriceHistoryModel)
            .filter(PriceHistoryModel.product_id == product_id)
            .order_by(desc(PriceHistoryModel.created_at))
            .all()
        )
        return [self._to_entity(r) for r in records]

    def get_latest_by_product_id(self, product_id: int) -> PriceHistoryEntity | None:
        """Return the most recent price record for a product."""
        db_record = (
            self.db.query(PriceHistoryModel)
            .filter(PriceHistoryModel.product_id == product_id)
            .order_by(desc(PriceHistoryModel.created_at))
            .first()
        )
        return self._to_entity(db_record) if db_record else None

    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[PriceHistoryEntity], int]:
        """Return a paginated list of all price records and the total count."""
        query = self.db.query(PriceHistoryModel)

        total = query.count()

        if sort_by and hasattr(PriceHistoryModel, sort_by):
            order_column = getattr(PriceHistoryModel, sort_by)
            query = query.order_by(
                desc(order_column) if sort_order == "desc" else asc(order_column)
            )
        else:
            query = query.order_by(desc(PriceHistoryModel.created_at))

        records = query.limit(limit).offset(offset).all()
        return [self._to_entity(r) for r in records], total

    def delete(self, price_history_id: int) -> bool:
        """Delete a price record by id."""
        db_record = (
            self.db.query(PriceHistoryModel)
            .filter(PriceHistoryModel.id == price_history_id)
            .first()
        )
        if not db_record:
            return False
        self.db.delete(db_record)
        self.db.commit()
        return True
