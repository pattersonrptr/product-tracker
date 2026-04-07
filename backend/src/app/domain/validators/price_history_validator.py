from src.app.interfaces.repositories.price_history_repository import (
    PriceHistoryRepositoryInterface,
)
from src.app.interfaces.repositories.product_repository import (
    ProductRepositoryInterface,
)
from src.common.jsonapi import JsonApiError


class PriceHistoryValidator:
    """Validates price history create requests."""

    def __init__(
        self,
        price_history_repo: PriceHistoryRepositoryInterface,
        product_repo: ProductRepositoryInterface,
    ):
        self.price_history_repo = price_history_repo
        self.product_repo = product_repo

    def validate_create_request(self, price_history_in) -> list[JsonApiError]:
        """
        Validates a price history creation request.
        Returns list of errors (empty if valid).
        """
        errors = []

        # Validation 1: type must be "price_history"
        if price_history_in.data.type != "price_history":
            errors.append(
                JsonApiError(
                    status="400",
                    code="INVALID_TYPE",
                    title="Invalid resource type",
                    detail=f"Expected type 'price_history', got '{price_history_in.data.type}'",
                    source={"pointer": "/data/type"},
                )
            )

        attrs = price_history_in.data.attributes

        # Validation 2: product_id required and positive
        if attrs.product_id is None or attrs.product_id <= 0:
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'product_id' must be a positive integer",
                    source={"pointer": "/data/attributes/product_id"},
                )
            )

        # Validation 3: price required and positive
        if attrs.price is None or attrs.price <= 0:
            errors.append(
                JsonApiError(
                    status="422",
                    code="INVALID_FIELD",
                    title="Validation error",
                    detail="Field 'price' must be a positive number",
                    source={"pointer": "/data/attributes/price"},
                )
            )

        # Return early if field-level errors
        if errors:
            return errors

        # Validation 4: referenced product must exist
        existing_product = self.product_repo.get_by_id(attrs.product_id)
        if not existing_product:
            errors.append(
                JsonApiError(
                    status="404",
                    code="PRODUCT_NOT_FOUND",
                    title="Related resource not found",
                    detail=f"Product with id '{attrs.product_id}' does not exist",
                    source={"pointer": "/data/attributes/product_id"},
                )
            )

        return errors
