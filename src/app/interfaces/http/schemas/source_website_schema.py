from datetime import datetime

from pydantic import BaseModel, Field

from src.common.jsonapi import (
    CollectionResponse,
    ResourceObject,
    ResourceObjectForCreation,
    SingleResourceRequest,
    SingleResourceResponse,
)


class SourceWebsiteAttributes(BaseModel):
    """Source website attributes for responses."""

    name: str
    base_url: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SourceWebsiteAttributesForCreation(BaseModel):
    """Attributes for source website creation."""

    name: str
    base_url: str
    is_active: bool = True


class SourceWebsiteAttributesForUpdate(BaseModel):
    """Attributes for source website update — all fields optional."""

    name: str | None = None
    base_url: str | None = None
    is_active: bool | None = None


class SourceWebsiteResource(ResourceObject):
    """Source website resource following JSON:API specification."""

    type: str = Field(default="source_websites", examples=["source_websites"])
    attributes: SourceWebsiteAttributes

    @classmethod
    def from_entity(cls, entity) -> "SourceWebsiteResource":
        """Factory method: converts a SourceWebsiteEntity to SourceWebsiteResource."""
        return cls.from_model(
            entity,
            type_name="source_websites",
            attributes_field=SourceWebsiteAttributes,
        )


class SourceWebsiteResourceForCreation(ResourceObjectForCreation):
    """ResourceObject for source website creation (without id)."""

    type: str = Field(default="source_websites", examples=["source_websites"])
    attributes: SourceWebsiteAttributesForCreation


class SourceWebsiteResourceForUpdate(ResourceObjectForCreation):
    """ResourceObject for source website update (without id)."""

    type: str = Field(default="source_websites", examples=["source_websites"])
    attributes: SourceWebsiteAttributesForUpdate


class SourceWebsiteCreateRequest(SingleResourceRequest):
    """Request schema for creating a source website."""

    data: SourceWebsiteResourceForCreation


class SourceWebsiteUpdateRequest(SingleResourceRequest):
    """Request schema for updating a source website."""

    data: SourceWebsiteResourceForUpdate


class SourceWebsiteReadResponse(SingleResourceResponse):
    """Response schema for a single source website."""

    data: SourceWebsiteResource


class SourceWebsitesCollectionResponse(CollectionResponse):
    """Response schema for a collection of source websites."""

    data: list[SourceWebsiteResource]
