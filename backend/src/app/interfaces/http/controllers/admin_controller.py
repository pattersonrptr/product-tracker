from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.app.entities.user import User as UserEntity
from src.app.infrastructure.database.models.price_alert_model import PriceAlert
from src.app.infrastructure.database.models.product_model import Product
from src.app.infrastructure.database.models.search_execution_log_model import (
    SearchExecutionLog,
)
from src.app.infrastructure.database.models.source_website_model import SourceWebsite
from src.app.infrastructure.database.models.user_model import User
from src.app.infrastructure.database_config import get_db
from src.app.security.auth import get_current_superuser

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary")
def get_admin_summary(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_superuser),
):
    total_users = db.query(func.count(User.id)).scalar()
    active_users = (
        db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar()
    )

    total_products = db.query(func.count(Product.id)).scalar()
    total_alerts = db.query(func.count(PriceAlert.id)).scalar()
    active_alerts = (
        db.query(func.count(PriceAlert.id))
        .filter(PriceAlert.is_active.is_(True))
        .scalar()
    )

    total_source_websites = db.query(func.count(SourceWebsite.id)).scalar()
    active_source_websites = (
        db.query(func.count(SourceWebsite.id))
        .filter(SourceWebsite.is_active.is_(True))
        .scalar()
    )

    recent_executions = (
        db.query(SearchExecutionLog)
        .order_by(SearchExecutionLog.started_at.desc())
        .limit(20)
        .all()
    )

    success_count = sum(1 for e in recent_executions if e.status == "success")
    failed_count = sum(1 for e in recent_executions if e.status == "failed")

    return {
        "data": {
            "type": "admin-summary",
            "id": "1",
            "attributes": {
                "total-users": total_users,
                "active-users": active_users,
                "total-products": total_products,
                "total-alerts": total_alerts,
                "active-alerts": active_alerts,
                "total-source-websites": total_source_websites,
                "active-source-websites": active_source_websites,
                "recent-executions": [
                    {
                        "id": e.id,
                        "search-config-id": e.search_config_id,
                        "status": e.status,
                        "results-count": e.results_count,
                        "error-message": e.error_message,
                        "started-at": e.started_at.isoformat()
                        if e.started_at
                        else None,
                        "finished-at": e.finished_at.isoformat()
                        if e.finished_at
                        else None,
                    }
                    for e in recent_executions
                ],
                "scraper-stats": {
                    "recent-total": len(recent_executions),
                    "success-count": success_count,
                    "failed-count": failed_count,
                },
            },
        }
    }
