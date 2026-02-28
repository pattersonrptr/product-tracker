from datetime import datetime

from pydantic import BaseModel, Field

from src.common.jsonapi import (
    CollectionResponse,
    ResourceObject,
    SingleResourceResponse,
)


class SearchExecutionLogAttributes(BaseModel):
    """Search execution log attributes for responses."""

    search_config_id: int
    status: str
    results_count: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SearchExecutionLogResource(ResourceObject):
    """Search execution log resource following JSON:API specification."""

    type: str = Field(
        default="search_execution_logs", examples=["search_execution_logs"]
    )
    attributes: SearchExecutionLogAttributes

    @classmethod
    def from_entity(cls, entity) -> "SearchExecutionLogResource":
        """Factory method: converts a SearchExecutionLogEntity to SearchExecutionLogResource."""
        return cls.from_model(
            entity,
            type_name="search_execution_logs",
            attributes_field=SearchExecutionLogAttributes,
        )


class SearchExecutionLogReadResponse(SingleResourceResponse):
    """Response schema for a single search execution log."""

    data: SearchExecutionLogResource


class SearchExecutionLogsCollectionResponse(CollectionResponse):
    """Response schema for a collection of search execution logs."""

    data: list[SearchExecutionLogResource]
