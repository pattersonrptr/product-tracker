from abc import ABC, abstractmethod

from src.app.entities.source_website import SourceWebsite as SourceWebsiteEntity


class SourceWebsiteRepositoryInterface(ABC):
    """
    Interface for SourceWebsite Repository operations.

    Defines the contract for all source website data access operations,
    following the Repository pattern from Domain-Driven Design.
    """

    @abstractmethod
    def create(self, source_website: SourceWebsiteEntity) -> SourceWebsiteEntity:
        """
        Create a new source website in the repository.

        Args:
            source_website: SourceWebsiteEntity with source website data

        Returns:
            SourceWebsiteEntity: Created source website with generated ID

        Raises:
            IntegrityError: If name constraint is violated (duplicate name)
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, source_website_id: int) -> SourceWebsiteEntity | None:
        """
        Retrieve a source website by its unique ID.

        Args:
            source_website_id: The unique identifier of the source website

        Returns:
            SourceWebsiteEntity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> SourceWebsiteEntity | None:
        """
        Retrieve a source website by its unique name.

        Args:
            name: The unique name of the source website

        Returns:
            SourceWebsiteEntity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[SourceWebsiteEntity], int]:
        """
        Retrieve all source websites with pagination and sorting.

        Args:
            limit: Maximum number of source websites to return
            offset: Number of source websites to skip
            sort_by: Field name to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Tuple of (list of SourceWebsiteEntity, total count)
        """
        raise NotImplementedError

    @abstractmethod
    def update(
        self, source_website_id: int, source_website: SourceWebsiteEntity
    ) -> SourceWebsiteEntity | None:
        """
        Update an existing source website's information.

        Args:
            source_website_id: The ID of the source website to update
            source_website: SourceWebsiteEntity with updated data

        Returns:
            Updated SourceWebsiteEntity if found, None otherwise

        Raises:
            IntegrityError: If update violates name uniqueness constraint
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, source_website_id: int) -> bool:
        """
        Delete a source website from the repository.

        Args:
            source_website_id: The ID of the source website to delete

        Returns:
            True if source website was deleted, False if not found
        """
        raise NotImplementedError
