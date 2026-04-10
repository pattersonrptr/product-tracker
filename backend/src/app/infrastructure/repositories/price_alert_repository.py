from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from src.app.entities.price_alert import PriceAlert as PriceAlertEntity
from src.app.infrastructure.database.models.price_alert_model import (
    PriceAlert as PriceAlertModel,
)
from src.app.infrastructure.database.models.source_website_model import (
    SourceWebsite as SourceWebsiteModel,
)
from src.app.interfaces.repositories.price_alert_repository import (
    PriceAlertRepositoryInterface,
)


class PriceAlertRepository(PriceAlertRepositoryInterface):
    """SQLAlchemy implementation of PriceAlertRepositoryInterface."""

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: PriceAlertModel) -> PriceAlertEntity:
        """Convert a PriceAlert ORM model to a domain entity."""
        return PriceAlertEntity(
            id=model.id,
            search_term=model.search_term,
            max_price=model.max_price,
            is_active=model.is_active,
            frequency_minutes=model.frequency_minutes,
            last_triggered_at=model.last_triggered_at,
            user_id=model.user_id,
            source_website_ids=[sw.id for sw in model.source_websites],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _sync_source_websites(
        self, db_model: PriceAlertModel, source_website_ids: list[int]
    ) -> None:
        """Sync the M2M source_websites relationship from a list of IDs."""
        db_model.source_websites.clear()
        if source_website_ids:
            source_websites = (
                self.db.query(SourceWebsiteModel)
                .filter(SourceWebsiteModel.id.in_(source_website_ids))
                .all()
            )
            db_model.source_websites.extend(source_websites)

    def create(self, price_alert: PriceAlertEntity) -> PriceAlertEntity:
        """Persist a new price alert and return it with assigned id."""
        db_price_alert = PriceAlertModel(
            search_term=price_alert.search_term,
            max_price=price_alert.max_price,
            is_active=price_alert.is_active,
            frequency_minutes=price_alert.frequency_minutes,
            last_triggered_at=price_alert.last_triggered_at,
            user_id=price_alert.user_id,
        )
        self.db.add(db_price_alert)
        self.db.flush()  # get the id before syncing M2M

        self._sync_source_websites(db_price_alert, price_alert.source_website_ids)

        self.db.commit()
        self.db.refresh(db_price_alert)
        return self._to_entity(db_price_alert)

    def get_by_id(self, price_alert_id: int) -> PriceAlertEntity | None:
        """Retrieve a price alert by its primary key."""
        db_record = (
            self.db.query(PriceAlertModel)
            .options(joinedload(PriceAlertModel.source_websites))
            .filter(PriceAlertModel.id == price_alert_id)
            .first()
        )
        return self._to_entity(db_record) if db_record else None

    def get_by_user_id(self, user_id: int) -> list[PriceAlertEntity]:
        """Return all price alerts for a given user."""
        records = (
            self.db.query(PriceAlertModel)
            .options(joinedload(PriceAlertModel.source_websites))
            .filter(PriceAlertModel.user_id == user_id)
            .all()
        )
        return [self._to_entity(r) for r in records]

    def get_by_search_term_and_user_id(
        self, search_term: str, user_id: int
    ) -> PriceAlertEntity | None:
        """Return a price alert matching term + user (for uniqueness check)."""
        db_record = (
            self.db.query(PriceAlertModel)
            .filter(
                PriceAlertModel.search_term == search_term,
                PriceAlertModel.user_id == user_id,
            )
            .first()
        )
        return self._to_entity(db_record) if db_record else None

    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[PriceAlertEntity], int]:
        """Return a paginated list of all price alerts and the total count."""
        query = self.db.query(PriceAlertModel).options(
            joinedload(PriceAlertModel.source_websites)
        )

        total = query.count()

        if sort_by and hasattr(PriceAlertModel, sort_by):
            order_column = getattr(PriceAlertModel, sort_by)
            query = query.order_by(
                desc(order_column) if sort_order == "desc" else asc(order_column)
            )

        records = query.offset(offset).limit(limit).all()
        return [self._to_entity(r) for r in records], total

    def update(
        self, price_alert_id: int, price_alert: PriceAlertEntity
    ) -> PriceAlertEntity | None:
        """Update a price alert. Returns updated entity or None if not found."""
        db_record = (
            self.db.query(PriceAlertModel)
            .options(joinedload(PriceAlertModel.source_websites))
            .filter(PriceAlertModel.id == price_alert_id)
            .first()
        )
        if not db_record:
            return None

        db_record.search_term = price_alert.search_term
        db_record.max_price = price_alert.max_price
        db_record.is_active = price_alert.is_active
        db_record.frequency_minutes = price_alert.frequency_minutes
        db_record.last_triggered_at = price_alert.last_triggered_at
        db_record.user_id = price_alert.user_id

        self._sync_source_websites(db_record, price_alert.source_website_ids)

        self.db.commit()
        self.db.refresh(db_record)
        return self._to_entity(db_record)

    def delete(self, price_alert_id: int) -> bool:
        """Delete a price alert by id. Returns True if deleted, False if not found."""
        db_record = (
            self.db.query(PriceAlertModel)
            .filter(PriceAlertModel.id == price_alert_id)
            .first()
        )
        if not db_record:
            return False
        self.db.delete(db_record)
        self.db.commit()
        return True
