from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db,require_permission
from app.models.user import User
from app.schemas.dashboard import (AlertsDashboardResponse, ChildCompleteProfileSummaryResponse,
    ExecutiveDashboardResponse, GlobalSearchResponse, OperationalDashboardResponse)
from app.services.dashboard_service import (alert_references, child_complete_profile,
    executive_dashboard, global_search, operational_dashboard)

router = APIRouter(tags=["Dashboards and Search"])

@router.get("/dashboard/executive", response_model=ExecutiveDashboardResponse)
def executive(db: Session = Depends(get_db), _: User = Depends(require_permission("dashboard.view"))):
    return executive_dashboard(db)

@router.get("/dashboard/operational", response_model=OperationalDashboardResponse)
def operational(db: Session = Depends(get_db), _: User = Depends(require_permission("dashboard.view"))):
    return operational_dashboard(db)

@router.get("/dashboard/alerts", response_model=AlertsDashboardResponse)
def alerts(db: Session = Depends(get_db), user: User = Depends(require_permission("dashboard.view"))):
    role_names = {role.name for role in user.roles}
    return alert_references(db, bool(role_names & {"Admin", "Manager"}))

@router.get("/children/{child_id}/complete-profile-summary", response_model=ChildCompleteProfileSummaryResponse)
def complete_profile(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("children.view"))):
    result = child_complete_profile(db, child_id)
    if not {role.name for role in user.roles} & {"Admin", "Manager"}:
        result.case_management["risk_level"] = None
        result.case_management["welfare_status"] = None
        result.case_management["critical_incident_count"] = 0
    return result

@router.get("/search/global", response_model=GlobalSearchResponse)
def search(q: str = Query(min_length=2), module: str | None = None,
           limit: int = Query(10, ge=1, le=25), db: Session = Depends(get_db),
           _: User = Depends(require_permission("dashboard.view"))):
    return global_search(db, q, module, limit)
