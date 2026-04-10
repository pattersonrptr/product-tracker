"""Unit tests for PriceAlert Use Cases."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.app.entities.price_alert import PriceAlert as PriceAlertEntity
from src.app.use_cases.price_alert_use_cases import (
    CreatePriceAlertUseCase,
    DeletePriceAlertUseCase,
    GetPriceAlertByIdUseCase,
    GetPriceAlertsByUserIdUseCase,
    ListPriceAlertsUseCase,
    UpdatePriceAlertUseCase,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_repo():
    return Mock()


@pytest.fixture
def sample_entity():
    return PriceAlertEntity(
        id=1,
        search_term="iPhone 13",
        max_price=2500.00,
        is_active=True,
        frequency_minutes=60,
        user_id=1,
        source_website_ids=[],
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )


@pytest.fixture
def new_entity():
    """Entity without id (before persistence)."""
    return PriceAlertEntity(
        search_term="Samsung S23",
        max_price=1800.00,
        is_active=True,
        frequency_minutes=30,
        user_id=2,
        source_website_ids=[],
    )


# ============================================================================
# Tests
# ============================================================================


class TestCreatePriceAlertUseCase:
    """Tests for CreatePriceAlertUseCase.execute"""

    def test_execute_calls_repo_and_returns_entity(
        self, mock_repo, new_entity, sample_entity
    ):
        """
        Given: A new entity and a mock repository
        When: execute is called
        Then: Repository.create is called and result returned
        """
        mock_repo.create.return_value = sample_entity

        use_case = CreatePriceAlertUseCase(mock_repo)
        result = use_case.execute(new_entity)

        mock_repo.create.assert_called_once_with(new_entity)
        assert result == sample_entity


class TestGetPriceAlertByIdUseCase:
    """Tests for GetPriceAlertByIdUseCase.execute"""

    def test_execute_returns_entity_when_found(self, mock_repo, sample_entity):
        """
        Given: Existing price alert id
        When: execute is called
        Then: Returns entity
        """
        mock_repo.get_by_id.return_value = sample_entity

        result = GetPriceAlertByIdUseCase(mock_repo).execute(1)

        mock_repo.get_by_id.assert_called_once_with(1)
        assert result == sample_entity

    def test_execute_returns_none_when_not_found(self, mock_repo):
        """
        Given: Non-existent id
        When: execute is called
        Then: Returns None
        """
        mock_repo.get_by_id.return_value = None

        result = GetPriceAlertByIdUseCase(mock_repo).execute(999)

        assert result is None


class TestGetPriceAlertsByUserIdUseCase:
    """Tests for GetPriceAlertsByUserIdUseCase.execute"""

    def test_execute_returns_list_of_entities(self, mock_repo, sample_entity):
        """
        Given: A user_id with existing alerts
        When: execute is called
        Then: Returns list of entities
        """
        mock_repo.get_by_user_id.return_value = [sample_entity]

        result = GetPriceAlertsByUserIdUseCase(mock_repo).execute(1)

        mock_repo.get_by_user_id.assert_called_once_with(1)
        assert result == [sample_entity]

    def test_execute_returns_empty_list_when_no_alerts(self, mock_repo):
        """
        Given: A user_id with no alerts
        When: execute is called
        Then: Returns empty list
        """
        mock_repo.get_by_user_id.return_value = []

        result = GetPriceAlertsByUserIdUseCase(mock_repo).execute(99)

        assert result == []


class TestListPriceAlertsUseCase:
    """Tests for ListPriceAlertsUseCase.execute"""

    def test_execute_returns_paginated_result(self, mock_repo, sample_entity):
        """
        Given: Multiple alerts in repo
        When: execute is called with pagination
        Then: Returns (list, total) tuple
        """
        mock_repo.get_all.return_value = ([sample_entity], 1)

        result, total = ListPriceAlertsUseCase(mock_repo).execute(limit=10, offset=0)

        mock_repo.get_all.assert_called_once_with(
            limit=10, offset=0, sort_by=None, sort_order=None
        )
        assert total == 1
        assert result == [sample_entity]

    def test_execute_passes_sorting_params(self, mock_repo):
        """
        Given: sort_by and sort_order provided
        When: execute is called
        Then: Passes those params to repo
        """
        mock_repo.get_all.return_value = ([], 0)

        ListPriceAlertsUseCase(mock_repo).execute(
            limit=5, offset=0, sort_by="created_at", sort_order="desc"
        )

        mock_repo.get_all.assert_called_once_with(
            limit=5, offset=0, sort_by="created_at", sort_order="desc"
        )


class TestUpdatePriceAlertUseCase:
    """Tests for UpdatePriceAlertUseCase.execute"""

    def test_execute_returns_updated_entity(self, mock_repo, sample_entity):
        """
        Given: Existing id and updated entity
        When: execute is called
        Then: Returns updated entity
        """
        updated = PriceAlertEntity(
            id=1,
            search_term="iPhone 14",
            max_price=3000.00,
            is_active=True,
            frequency_minutes=120,
            user_id=1,
            source_website_ids=[],
        )
        mock_repo.update.return_value = updated

        result = UpdatePriceAlertUseCase(mock_repo).execute(1, sample_entity)

        mock_repo.update.assert_called_once_with(1, sample_entity)
        assert result == updated

    def test_execute_returns_none_when_not_found(self, mock_repo, sample_entity):
        """
        Given: Non-existent id
        When: execute is called
        Then: Returns None
        """
        mock_repo.update.return_value = None

        result = UpdatePriceAlertUseCase(mock_repo).execute(999, sample_entity)

        assert result is None


class TestDeletePriceAlertUseCase:
    """Tests for DeletePriceAlertUseCase.execute"""

    def test_execute_returns_true_when_deleted(self, mock_repo):
        """
        Given: Existing id
        When: execute is called
        Then: Returns True
        """
        mock_repo.delete.return_value = True

        result = DeletePriceAlertUseCase(mock_repo).execute(1)

        mock_repo.delete.assert_called_once_with(1)
        assert result is True

    def test_execute_returns_false_when_not_found(self, mock_repo):
        """
        Given: Non-existent id
        When: execute is called
        Then: Returns False
        """
        mock_repo.delete.return_value = False

        result = DeletePriceAlertUseCase(mock_repo).execute(999)

        assert result is False
