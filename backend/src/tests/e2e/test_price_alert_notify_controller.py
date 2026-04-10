"""
E2E Integration Tests for POST /price-alerts/{id}/notify

Tests the full flow: product saved → alert evaluated → notification enqueued.

Strategy: Uses the real repository stack with an in-memory SQLite database.
The email service is dependency-injected via app.dependency_overrides so no
real emails are sent.
"""

from unittest.mock import MagicMock

import pytest
from passlib.context import CryptContext

from src.app.infrastructure.database.models.notification_log_model import (
    NotificationLog as NotificationLogModel,
)
from src.app.infrastructure.database.models.price_alert_model import (
    PriceAlert as PriceAlertModel,
)
from src.app.infrastructure.database.models.price_alert_source_website_model import (
    price_alert_source_website,
)
from src.app.infrastructure.database.models.price_history_model import (
    PriceHistory as PriceHistoryModel,
)
from src.app.infrastructure.database.models.product_model import (
    Product as ProductModel,
)
from src.app.infrastructure.database.models.source_website_model import (
    SourceWebsite as SourceWebsiteModel,
)
from src.app.infrastructure.database.models.user_model import User
from src.app.infrastructure.services.email_service import (
    EmailResult,
    EmailServiceInterface,
)
from src.app.interfaces.http.controllers.price_alert_controller import get_email_service
from src.main import app

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def mock_email_service():
    """Return a mock email service that always reports a successful send."""
    svc = MagicMock(spec=EmailServiceInterface)
    svc.send_price_alert_email.return_value = EmailResult(success=True, status_code=202)
    return svc


@pytest.fixture
def client_with_email_mock(client, mock_email_service):
    """Override the email service dependency for tests in this module."""
    app.dependency_overrides[get_email_service] = lambda: mock_email_service
    yield client
    app.dependency_overrides.pop(get_email_service, None)


@pytest.fixture
def alert_owner(test_db):
    """Create a regular user who owns a price alert."""
    user = User(
        username="alertowner",
        email="alertowner@example.com",
        hashed_password=pwd_context.hash("Owner@1234"),
        is_superuser=False,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def source_website(test_db):
    """Create a source website for use in price alerts and products."""
    sw = SourceWebsiteModel(
        name="Test Market",
        base_url="https://testmarket.example.com",
        is_active=True,
    )
    test_db.add(sw)
    test_db.commit()
    test_db.refresh(sw)
    return sw


@pytest.fixture
def price_alert(test_db, alert_owner, source_website):
    """Create an active price alert searching for 'laptop' at max R$3000."""
    alert = PriceAlertModel(
        search_term="laptop",
        max_price=3000.00,
        is_active=True,
        frequency_minutes=60,
        user_id=alert_owner.id,
    )
    test_db.add(alert)
    test_db.flush()
    # Associate with the source website
    test_db.execute(
        price_alert_source_website.insert().values(
            price_alert_id=alert.id, source_website_id=source_website.id
        )
    )
    test_db.commit()
    test_db.refresh(alert)
    return alert


@pytest.fixture
def matching_product(test_db, source_website):
    """Create a product that matches the price alert (price below max)."""
    product = ProductModel(
        url="https://testmarket.example.com/laptop/1",
        title="laptop gamer 16GB",
        source_website_id=source_website.id,
        is_available=True,
    )
    test_db.add(product)
    test_db.flush()
    # Add price history so current_price is available
    history = PriceHistoryModel(product_id=product.id, price=2500.00)
    test_db.add(history)
    test_db.commit()
    test_db.refresh(product)
    return product


# ===========================================================================
# Tests
# ===========================================================================


class TestPriceAlertNotifyEndpoint:
    """Integration tests for POST /price-alerts/{id}/notify"""

    def test_notify_skips_when_alert_not_found(
        self, client_with_email_mock, staff_auth_headers
    ):
        """Returns 404 when the price alert does not exist."""
        response = client_with_email_mock.post(
            "/price-alerts/99999/notify",
            headers=staff_auth_headers,
        )
        assert response.status_code == 404

    def test_notify_skips_when_no_matching_product(
        self,
        client_with_email_mock,
        staff_auth_headers,
        price_alert,
        mock_email_service,
    ):
        """
        Given: An active price alert with no matching products
        When: POST /price-alerts/{id}/notify
        Then: Returns 200 with status=skipped and sends no email
        """
        response = client_with_email_mock.post(
            f"/price-alerts/{price_alert.id}/notify",
            headers=staff_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]["attributes"]
        assert data["status"] == "skipped"
        assert data["notifications_sent"] == 0
        mock_email_service.send_price_alert_email.assert_not_called()

    def test_full_flow_product_save_alert_match_notification_sent(
        self,
        client_with_email_mock,
        staff_auth_headers,
        price_alert,
        matching_product,
        mock_email_service,
        test_db,
    ):
        """
        Full flow: product exists below max_price → alert evaluated → email sent.

        Given: An active price alert and a matching product below max_price
        When: POST /price-alerts/{id}/notify
        Then: Returns 200 with status=sent, email was called, notification log created
        """
        response = client_with_email_mock.post(
            f"/price-alerts/{price_alert.id}/notify",
            headers=staff_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]["attributes"]
        assert data["status"] == "sent"
        assert data["notifications_sent"] == 1

        # Email was actually dispatched
        mock_email_service.send_price_alert_email.assert_called_once()
        call_kwargs = mock_email_service.send_price_alert_email.call_args[1]
        assert call_kwargs["search_term"] == "laptop"
        assert call_kwargs["product_price"] == 2500.00
        assert call_kwargs["max_price"] == 3000.00

        # Notification log was persisted
        logs = (
            test_db.query(NotificationLogModel)
            .filter(NotificationLogModel.price_alert_id == price_alert.id)
            .all()
        )
        assert len(logs) == 1
        assert logs[0].status == "sent"
        assert logs[0].product_id == matching_product.id

    def test_duplicate_notification_skipped_for_same_product_and_alert(
        self,
        client_with_email_mock,
        staff_auth_headers,
        price_alert,
        matching_product,
        mock_email_service,
        test_db,
    ):
        """
        Dedup: second notify call for the same product+alert pair is skipped.

        Given: A notification was already sent for product+alert
        When: POST /price-alerts/{id}/notify is called again
        Then: Returns 200 with status=skipped, no second email sent
        """
        # First call — should succeed
        first = client_with_email_mock.post(
            f"/price-alerts/{price_alert.id}/notify",
            headers=staff_auth_headers,
        )
        assert first.status_code == 200
        assert first.json()["data"]["attributes"]["status"] == "sent"

        # Reset mock call count to track second call independently
        mock_email_service.send_price_alert_email.reset_mock()

        # Second call — same product+alert, should be deduped
        second = client_with_email_mock.post(
            f"/price-alerts/{price_alert.id}/notify",
            headers=staff_auth_headers,
        )
        assert second.status_code == 200
        data = second.json()["data"]["attributes"]
        assert data["status"] == "skipped"
        assert data["notifications_sent"] == 0
        mock_email_service.send_price_alert_email.assert_not_called()

    def test_notify_requires_staff_or_superuser_access(self, client, user_token, price_alert):
        """Regular users cannot trigger notifications — requires staff/superuser."""
        response = client.post(
            f"/price-alerts/{price_alert.id}/notify",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
