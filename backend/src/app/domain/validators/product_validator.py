from src.app.interfaces.http.schemas.product_schema import (
    ProductCreateRequest,
    ProductUpdateRequest,
)
from src.app.interfaces.repositories.product_repository import (
    ProductRepositoryInterface,
)
from src.common.jsonapi import JsonApiError


class ProductValidator:
    def __init__(self, product_repo: ProductRepositoryInterface):
        self.product_repo = product_repo

    def validate_create_request(
        self, product_in: ProductCreateRequest
    ) -> list[JsonApiError]:
        """
        Validates a product creation request.
        Returns list of errors (empty if valid).
        """
        errors = []

        # Validation 1: type must be "product"
        if product_in.data.type != "product":
            errors.append(
                JsonApiError(
                    status="400",
                    code="INVALID_TYPE",
                    title="Invalid resource type",
                    detail=f"Expected type 'product', got '{product_in.data.type}'",
                    source={"pointer": "/data/type"},
                )
            )

        attrs = product_in.data.attributes

        # Validation 2: URL required
        if not attrs.url or not attrs.url.strip():
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'url' is required",
                    source={"pointer": "/data/attributes/url"},
                )
            )

        # Validation 3: title required
        if not attrs.title or not attrs.title.strip():
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'title' is required",
                    source={"pointer": "/data/attributes/title"},
                )
            )

        # Validation 4: source_website_id required
        if attrs.source_website_id is None:
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'source_website_id' is required",
                    source={"pointer": "/data/attributes/source_website_id"},
                )
            )

        # If there are required field errors, return early (don't validate duplicates)
        if errors:
            return errors

        # Validation 5: URL already exists
        if attrs.url:
            existing_product = self.product_repo.get_by_url(attrs.url)
            if existing_product:
                errors.append(
                    JsonApiError(
                        status="409",
                        code="DUPLICATE_URL",
                        title="Conflict",
                        detail=f"A product with URL '{attrs.url}' already exists",
                        source={"pointer": "/data/attributes/url"},
                    )
                )

        return errors

    def validate_update_request(
        self, product_id: int, product_in: ProductUpdateRequest
    ) -> list[JsonApiError]:
        """
        Validates a product update request.
        Returns list of errors (empty if valid).
        """
        errors = []

        # Validation 1: type must be "product"
        if product_in.data.type != "product":
            errors.append(
                JsonApiError(
                    status="400",
                    code="INVALID_TYPE",
                    title="Invalid resource type",
                    detail=f"Expected type 'product', got '{product_in.data.type}'",
                    source={"pointer": "/data/type"},
                )
            )

        attrs = product_in.data.attributes

        # Validation 2: title cannot be empty if provided
        if attrs.title is not None and not attrs.title.strip():
            errors.append(
                JsonApiError(
                    status="422",
                    code="INVALID_VALUE",
                    title="Validation error",
                    detail="Field 'title' cannot be empty",
                    source={"pointer": "/data/attributes/title"},
                )
            )

        # Validation 3: URL cannot be changed to a duplicate if provided
        if attrs.url is not None:
            if not attrs.url.strip():
                errors.append(
                    JsonApiError(
                        status="422",
                        code="INVALID_VALUE",
                        title="Validation error",
                        detail="Field 'url' cannot be empty",
                        source={"pointer": "/data/attributes/url"},
                    )
                )
            else:
                # Check if URL is being changed to a different product's URL
                existing_product = self.product_repo.get_by_url(attrs.url)
                if existing_product and existing_product.id != product_id:
                    errors.append(
                        JsonApiError(
                            status="409",
                            code="DUPLICATE_URL",
                            title="Conflict",
                            detail=f"A product with URL '{attrs.url}' already exists",
                            source={"pointer": "/data/attributes/url"},
                        )
                    )

        return errors
