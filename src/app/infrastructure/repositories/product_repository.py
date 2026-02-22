from datetime import UTC, datetime

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from src.app.entities.product import Product as ProductEntity
from src.app.infrastructure.database.models.product_model import Product as ProductModel
from src.app.interfaces.repositories.product_repository import (
    ProductRepositoryInterface,
)


class ProductRepository(ProductRepositoryInterface):
    """SQLAlchemy implementation of ProductRepositoryInterface."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, product: ProductEntity) -> ProductEntity:
        """Create a new product in the database."""
        db_product = ProductModel(**product.model_dump(exclude={"id", "current_price"}))
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return self._to_entity(db_product)

    def get_by_id(self, product_id: int) -> ProductEntity | None:
        """Retrieve a product by ID with source_website relationship."""
        product = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.source_website))
            .filter(ProductModel.id == product_id)
            .first()
        )
        if product:
            return self._to_entity(product)
        return None

    def get_by_url(self, url: str) -> ProductEntity | None:
        """Retrieve a product by URL."""
        product = (
            self.db.query(ProductModel)
            .options(joinedload(ProductModel.source_website))
            .filter(ProductModel.url == url)
            .first()
        )
        if product:
            return self._to_entity(product)
        return None

    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[ProductEntity], int]:
        """Retrieve all products with pagination and sorting."""
        query = self.db.query(ProductModel).options(
            joinedload(ProductModel.source_website)
        )

        # Get total count
        total = query.count()

        # Apply sorting
        if sort_by and hasattr(ProductModel, sort_by):
            order_column = getattr(ProductModel, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        else:
            # Default sorting by created_at desc
            query = query.order_by(desc(ProductModel.created_at))

        # Apply pagination
        products = query.limit(limit).offset(offset).all()

        return [self._to_entity(product) for product in products], total

    def update(self, product_id: int, product: ProductEntity) -> ProductEntity | None:
        """Update an existing product."""
        db_product = (
            self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
        )
        if not db_product:
            return None

        try:
            for key, value in product.model_dump(
                exclude_unset=True, exclude={"id", "current_price"}
            ).items():
                setattr(db_product, key, value)

            db_product.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(db_product)
            return self._to_entity(db_product)
        except Exception as e:
            self.db.rollback()
            raise e

    def delete(self, product_id: int) -> bool:
        """Delete a product from the database."""
        db_product = (
            self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
        )
        if not db_product:
            return False

        try:
            self.db.delete(db_product)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def _to_entity(self, product_model: ProductModel) -> ProductEntity:
        """
        Convert ProductModel to ProductEntity.

        Calculates current_price from price_history relationship when available.
        """
        product_dict = {
            "id": product_model.id,
            "url": product_model.url,
            "title": product_model.title,
            "source_product_code": product_model.source_product_code,
            "description": product_model.description,
            "image_urls": product_model.image_urls,
            "city": product_model.city,
            "state": product_model.state,
            "condition": product_model.condition,
            "seller_name": product_model.seller_name,
            "is_available": product_model.is_available,
            "source_website_id": product_model.source_website_id,
            "source_metadata": product_model.source_metadata,
            "created_at": product_model.created_at,
            "updated_at": product_model.updated_at,
            "current_price": None,  # Will be populated from price_history later
        }
        return ProductEntity(**product_dict)
