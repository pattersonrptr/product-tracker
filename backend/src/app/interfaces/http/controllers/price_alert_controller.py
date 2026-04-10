from fastapi import APIRouter, Depends, Query

from src.app.domain.validators.price_alert_validator import PriceAlertValidator
from src.app.entities.price_alert import PriceAlert as PriceAlertEntity
from src.app.entities.user import User as UserEntity
from src.app.infrastructure.database_config import get_db
from src.app.infrastructure.repositories.price_alert_repository import (
    PriceAlertRepository,
)
from src.app.infrastructure.repositories.product_repository import ProductRepository
from src.app.infrastructure.repositories.search_config_repository import (
    SearchConfigRepository,
)
from src.app.infrastructure.repositories.source_website_repository import (
    SourceWebsiteRepository,
)
from src.app.interfaces.http.presenters.price_alert_presenter import (
    PriceAlertPresenter,
)
from src.app.interfaces.http.presenters.product_presenter import ProductPresenter
from src.app.interfaces.http.schemas.price_alert_schema import (
    PriceAlertCreateRequest,
    PriceAlertReadResponse,
    PriceAlertsCollectionResponse,
    PriceAlertUpdateRequest,
)
from src.app.interfaces.http.schemas.product_schema import ProductsCollectionResponse
from src.app.security.auth import get_current_staff_user
from src.app.use_cases.price_alert_use_cases import (
    CreatePriceAlertUseCase,
    DeletePriceAlertUseCase,
    GetPriceAlertByIdUseCase,
    GetPriceAlertsByUserIdUseCase,
    GetProductsByPriceAlertUseCase,
    ListPriceAlertsUseCase,
    UpdatePriceAlertUseCase,
)
from src.config.logging_config import get_logger

router = APIRouter(tags=["price_alerts"], prefix="/price-alerts")

logger = get_logger(__name__)


def get_price_alert_repository(db=Depends(get_db)) -> PriceAlertRepository:
    """Dependency injection for PriceAlertRepository."""
    return PriceAlertRepository(db)


def get_search_config_repository(db=Depends(get_db)) -> SearchConfigRepository:
    """Dependency injection for SearchConfigRepository."""
    return SearchConfigRepository(db)


def get_product_repository(db=Depends(get_db)) -> ProductRepository:
    """Dependency injection for ProductRepository."""
    return ProductRepository(db)


def get_source_website_repository(db=Depends(get_db)) -> SourceWebsiteRepository:
    """Dependency injection for SourceWebsiteRepository (used by validator)."""
    return SourceWebsiteRepository(db)


def get_price_alert_validator(
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    source_website_repo: SourceWebsiteRepository = Depends(
        get_source_website_repository
    ),
) -> PriceAlertValidator:
    """Dependency injection for PriceAlertValidator."""
    return PriceAlertValidator(price_alert_repo, source_website_repo)


@router.post("/", response_model=PriceAlertReadResponse, status_code=201)
def create_price_alert(
    price_alert_in: PriceAlertCreateRequest,
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    search_config_repo: SearchConfigRepository = Depends(get_search_config_repository),
    price_alert_validator: PriceAlertValidator = Depends(get_price_alert_validator),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Create a new price alert. Requires staff or superuser access.

    Automatically creates or reuses a SearchConfig matching the alert's
    search_term and source_website_ids for the same user.

    Returns:
        - 201: Price alert created successfully
        - 400: Validation errors (invalid type)
        - 403: Permission denied
        - 404: Referenced source website not found
        - 409: Duplicate search term for this user
        - 422: Invalid field values
    """
    logger.info(
        f"Creating new price alert: '{price_alert_in.data.attributes.search_term}'",
        extra={"action": "create_price_alert", "user_id": current_user.id},
    )

    validation_errors = price_alert_validator.validate_create_request(price_alert_in)
    if validation_errors:
        logger.warning(
            f"Price alert creation validation failed: {len(validation_errors)} errors",
            extra={
                "action": "price_alert_validation_failed",
                "user_id": current_user.id,
            },
        )
        return PriceAlertPresenter.handle_validation_errors(validation_errors)

    attrs = price_alert_in.data.attributes
    price_alert_entity = PriceAlertEntity(
        search_term=attrs.search_term,
        max_price=attrs.max_price,
        is_active=attrs.is_active,
        frequency_minutes=attrs.frequency_minutes,
        user_id=attrs.user_id,
        source_website_ids=attrs.source_website_ids,
    )

    use_case = CreatePriceAlertUseCase(price_alert_repo, search_config_repo)
    created = use_case.execute(price_alert_entity)

    logger.info(
        f"Price alert created: '{created.search_term}' (ID: {created.id})",
        extra={
            "action": "price_alert_created",
            "price_alert_id": created.id,
            "user_id": current_user.id,
        },
    )
    return PriceAlertPresenter.handle_success(created)


@router.get("/", response_model=PriceAlertsCollectionResponse)
def list_price_alerts(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default="desc", pattern="^(asc|desc)$"),
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    List all price alerts with pagination. Requires staff or superuser access.

    Returns:
        - 200: Collection of price alerts with pagination meta
        - 403: Permission denied
    """
    logger.debug(
        f"Listing price alerts: limit={limit}, offset={offset}",
        extra={"action": "list_price_alerts", "user_id": current_user.id},
    )

    use_case = ListPriceAlertsUseCase(price_alert_repo)
    price_alerts, total = use_case.execute(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PriceAlertPresenter.handle_collection_success(price_alerts, total)


@router.get("/user/{user_id}", response_model=PriceAlertsCollectionResponse)
def get_price_alerts_by_user(
    user_id: int,
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Get all price alerts for a specific user. Requires staff or superuser access.

    Returns:
        - 200: Collection of price alerts for the user
        - 403: Permission denied
    """
    logger.debug(
        f"Getting price alerts for user_id: {user_id}",
        extra={
            "action": "get_price_alerts_by_user",
            "target_user_id": user_id,
            "user_id": current_user.id,
        },
    )

    use_case = GetPriceAlertsByUserIdUseCase(price_alert_repo)
    price_alerts = use_case.execute(user_id)
    return PriceAlertPresenter.handle_collection_success(
        price_alerts, len(price_alerts)
    )


@router.get("/{price_alert_id}", response_model=PriceAlertReadResponse)
def get_price_alert(
    price_alert_id: int,
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Get a single price alert by ID. Requires staff or superuser access.

    Returns:
        - 200: Price alert found
        - 403: Permission denied
        - 404: Price alert not found
    """
    logger.debug(
        f"Getting price alert ID: {price_alert_id}",
        extra={
            "action": "get_price_alert",
            "price_alert_id": price_alert_id,
            "user_id": current_user.id,
        },
    )

    use_case = GetPriceAlertByIdUseCase(price_alert_repo)
    price_alert = use_case.execute(price_alert_id)

    if not price_alert:
        return PriceAlertPresenter.handle_not_found(f"id {price_alert_id}", "/data/id")

    return PriceAlertPresenter.handle_success(price_alert)


@router.get("/{price_alert_id}/products", response_model=ProductsCollectionResponse)
def get_products_by_price_alert(
    price_alert_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    filter_by_max_price: bool = Query(
        default=True,
        description="When true, only return products at or below the alert's max_price",
    ),
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Get products matching a price alert's criteria, sorted by price ascending.

    Searches products whose title matches the alert's search_term and
    belong to one of the alert's source websites. By default, only
    products at or below the alert's max_price are returned.

    Returns:
        - 200: Collection of matching products with pagination meta
        - 403: Permission denied
        - 404: Price alert not found
    """
    logger.debug(
        f"Getting products for price alert ID: {price_alert_id}",
        extra={
            "action": "get_products_by_price_alert",
            "price_alert_id": price_alert_id,
            "user_id": current_user.id,
        },
    )

    use_case = GetProductsByPriceAlertUseCase(price_alert_repo, product_repo)
    alert, products, total = use_case.execute(
        price_alert_id,
        limit=limit,
        offset=offset,
        filter_by_max_price=filter_by_max_price,
    )

    if not alert:
        return PriceAlertPresenter.handle_not_found(f"id {price_alert_id}", "/data/id")

    return ProductPresenter.handle_collection_success(products, total)


@router.put("/{price_alert_id}", response_model=PriceAlertReadResponse)
def update_price_alert(
    price_alert_id: int,
    price_alert_in: PriceAlertUpdateRequest,
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    search_config_repo: SearchConfigRepository = Depends(get_search_config_repository),
    price_alert_validator: PriceAlertValidator = Depends(get_price_alert_validator),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Update an existing price alert. Requires staff or superuser access.

    If search_term or source_website_ids change, the linked SearchConfig is
    updated accordingly.  Deactivating an alert will deactivate its
    SearchConfig if no other active alert references it.

    Returns:
        - 200: Price alert updated successfully
        - 400: Validation errors (invalid type)
        - 403: Permission denied
        - 404: Price alert not found
        - 409: Duplicate search term for same user
        - 422: Invalid field values
    """
    logger.info(
        f"Updating price alert ID: {price_alert_id}",
        extra={
            "action": "update_price_alert",
            "price_alert_id": price_alert_id,
            "user_id": current_user.id,
        },
    )

    get_uc = GetPriceAlertByIdUseCase(price_alert_repo)
    existing = get_uc.execute(price_alert_id)

    if not existing:
        return PriceAlertPresenter.handle_not_found(f"id {price_alert_id}", "/data/id")

    validation_errors = price_alert_validator.validate_update_request(
        price_alert_id, price_alert_in
    )
    if validation_errors:
        logger.warning(
            f"Price alert update validation failed: {len(validation_errors)} errors",
            extra={
                "action": "price_alert_update_validation_failed",
                "price_alert_id": price_alert_id,
            },
        )
        return PriceAlertPresenter.handle_validation_errors(validation_errors)

    attrs = price_alert_in.data.attributes
    updated_entity = PriceAlertEntity(
        id=price_alert_id,
        search_term=attrs.search_term
        if attrs.search_term is not None
        else existing.search_term,
        max_price=attrs.max_price
        if attrs.max_price is not None
        else existing.max_price,
        is_active=attrs.is_active
        if attrs.is_active is not None
        else existing.is_active,
        frequency_minutes=attrs.frequency_minutes
        if attrs.frequency_minutes is not None
        else existing.frequency_minutes,
        last_triggered_at=existing.last_triggered_at,
        user_id=existing.user_id,
        search_config_id=existing.search_config_id,
        source_website_ids=attrs.source_website_ids
        if attrs.source_website_ids is not None
        else existing.source_website_ids,
    )

    update_uc = UpdatePriceAlertUseCase(price_alert_repo, search_config_repo)
    updated = update_uc.execute(price_alert_id, updated_entity)

    logger.info(
        f"Price alert updated: '{updated.search_term}' (ID: {price_alert_id})",
        extra={
            "action": "price_alert_updated",
            "price_alert_id": price_alert_id,
            "user_id": current_user.id,
        },
    )
    return PriceAlertPresenter.handle_success(updated)


@router.delete("/{price_alert_id}", status_code=204)
def delete_price_alert(
    price_alert_id: int,
    price_alert_repo: PriceAlertRepository = Depends(get_price_alert_repository),
    search_config_repo: SearchConfigRepository = Depends(get_search_config_repository),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Delete a price alert. Requires staff or superuser access.

    If the associated SearchConfig is no longer used by any other active
    alert, it will be deactivated automatically.

    Returns:
        - 204: Deleted successfully (no content)
        - 403: Permission denied
        - 404: Price alert not found
    """
    logger.warning(
        f"Deleting price alert ID: {price_alert_id}",
        extra={
            "action": "delete_price_alert",
            "price_alert_id": price_alert_id,
            "user_id": current_user.id,
        },
    )

    get_uc = GetPriceAlertByIdUseCase(price_alert_repo)
    price_alert = get_uc.execute(price_alert_id)

    if not price_alert:
        return PriceAlertPresenter.handle_not_found(f"id {price_alert_id}", "/data/id")

    delete_uc = DeletePriceAlertUseCase(price_alert_repo, search_config_repo)
    deleted = delete_uc.execute(price_alert_id)

    if not deleted:
        return PriceAlertPresenter.handle_not_found(f"id {price_alert_id}", "/data/id")

    logger.warning(
        f"Price alert deleted (ID: {price_alert_id})",
        extra={
            "action": "price_alert_deleted",
            "price_alert_id": price_alert_id,
            "user_id": current_user.id,
        },
    )
    return None
