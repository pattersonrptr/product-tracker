from src.app.entities.source_website import SourceWebsite as SourceWebsiteEntity
from src.app.interfaces.repositories.source_website_repository import (
    SourceWebsiteRepositoryInterface,
)


class CreateSourceWebsiteUseCase:
    """Creates a new source website."""

    def __init__(self, source_website_repo: SourceWebsiteRepositoryInterface):
        self.source_website_repo = source_website_repo

    def execute(self, source_website: SourceWebsiteEntity) -> SourceWebsiteEntity:
        return self.source_website_repo.create(source_website)


class GetSourceWebsiteByIdUseCase:
    """Retrieves a source website by its ID."""

    def __init__(self, source_website_repo: SourceWebsiteRepositoryInterface):
        self.source_website_repo = source_website_repo

    def execute(self, source_website_id: int) -> SourceWebsiteEntity | None:
        return self.source_website_repo.get_by_id(source_website_id)


class GetSourceWebsiteByNameUseCase:
    """Retrieves a source website by its name."""

    def __init__(self, source_website_repo: SourceWebsiteRepositoryInterface):
        self.source_website_repo = source_website_repo

    def execute(self, name: str) -> SourceWebsiteEntity | None:
        return self.source_website_repo.get_by_name(name)


class ListSourceWebsitesUseCase:
    """Lists source websites with pagination and sorting."""

    def __init__(self, source_website_repo: SourceWebsiteRepositoryInterface):
        self.source_website_repo = source_website_repo

    def execute(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[SourceWebsiteEntity], int]:
        return self.source_website_repo.get_all(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )


class UpdateSourceWebsiteUseCase:
    """Updates an existing source website."""

    def __init__(self, source_website_repo: SourceWebsiteRepositoryInterface):
        self.source_website_repo = source_website_repo

    def execute(
        self, source_website_id: int, source_website: SourceWebsiteEntity
    ) -> SourceWebsiteEntity | None:
        return self.source_website_repo.update(source_website_id, source_website)


class DeleteSourceWebsiteUseCase:
    """Deletes a source website."""

    def __init__(self, source_website_repo: SourceWebsiteRepositoryInterface):
        self.source_website_repo = source_website_repo

    def execute(self, source_website_id: int) -> bool:
        return self.source_website_repo.delete(source_website_id)
