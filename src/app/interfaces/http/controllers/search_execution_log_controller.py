from fastapi import APIRouter, Depends, Query

from src.app.entities.user import User as UserEntity
from src.app.infrastructure.database_config import get_db
from src.app.infrastructure.repositories.search_execution_log_repository import (
    SearchExecutionLogRepository,
)
from src.app.interfaces.http.presenters.search_execution_log_presenter import (
    SearchExecutionLogPresenter,
)
from src.app.interfaces.http.schemas.search_execution_log_schema import (
    SearchExecutionLogReadResponse,
    SearchExecutionLogsCollectionResponse,
)
from src.app.security.auth import get_current_staff_user
from src.app.use_cases.search_execution_log_use_cases import (
    GetSearchExecutionLogByIdUseCase,
    GetSearchExecutionLogsBySearchConfigIdUseCase,
    ListSearchExecutionLogsUseCase,
)
from src.config.logging_config import get_logger

router = APIRouter(tags=["search_execution_logs"], prefix="/search-execution-logs")

logger = get_logger(__name__)


def get_search_execution_log_repository(
    db=Depends(get_db),
) -> SearchExecutionLogRepository:
    """Dependency injection for SearchExecutionLogRepository."""
    return SearchExecutionLogRepository(db)


@router.get("/", response_model=SearchExecutionLogsCollectionResponse)
def list_search_execution_logs(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default="desc", pattern="^(asc|desc)$"),
    search_execution_log_repo: SearchExecutionLogRepository = Depends(
        get_search_execution_log_repository
    ),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    List all search execution logs with pagination. Requires staff or superuser access.

    Returns:
        - 200: Collection of search execution logs with pagination meta
        - 403: Permission denied
    """
    logger.debug(
        f"Listing search execution logs: limit={limit}, offset={offset}",
        extra={"action": "list_search_execution_logs", "user_id": current_user.id},
    )

    use_case = ListSearchExecutionLogsUseCase(search_execution_log_repo)
    records, total = use_case.execute(
        limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
    )
    return SearchExecutionLogPresenter.handle_collection_success(records, total)


@router.get(
    "/search-config/{search_config_id}",
    response_model=SearchExecutionLogsCollectionResponse,
)
def get_search_execution_logs_by_search_config(
    search_config_id: int,
    search_execution_log_repo: SearchExecutionLogRepository = Depends(
        get_search_execution_log_repository
    ),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Get all search execution logs for a given search config.
    Requires staff or superuser access.

    Returns:
        - 200: Collection of search execution logs
        - 403: Permission denied
    """
    logger.debug(
        f"Getting search execution logs for search_config_id: {search_config_id}",
        extra={
            "action": "get_search_execution_logs_by_search_config",
            "user_id": current_user.id,
        },
    )

    use_case = GetSearchExecutionLogsBySearchConfigIdUseCase(search_execution_log_repo)
    records = use_case.execute(search_config_id)
    return SearchExecutionLogPresenter.handle_collection_success(records, len(records))


@router.get("/{search_execution_log_id}", response_model=SearchExecutionLogReadResponse)
def get_search_execution_log(
    search_execution_log_id: int,
    search_execution_log_repo: SearchExecutionLogRepository = Depends(
        get_search_execution_log_repository
    ),
    current_user: UserEntity = Depends(get_current_staff_user),
):
    """
    Get a single search execution log by ID. Requires staff or superuser access.

    Returns:
        - 200: Search execution log found
        - 403: Permission denied
        - 404: Not found
    """
    logger.debug(
        f"Getting search execution log ID: {search_execution_log_id}",
        extra={
            "action": "get_search_execution_log",
            "user_id": current_user.id,
        },
    )

    use_case = GetSearchExecutionLogByIdUseCase(search_execution_log_repo)
    record = use_case.execute(search_execution_log_id)

    if not record:
        return SearchExecutionLogPresenter.handle_not_found(
            f"id {search_execution_log_id}", "/data/id"
        )

    return SearchExecutionLogPresenter.handle_success(record)
