from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import can_operational_read, get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.consolidated_reports import AuditRanking, AuditSummaryResponse, ConsolidatedReportResponse
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Consolidated Reports"])

def paging(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    return limit, offset

@router.get("/consolidated/children", response_model=ConsolidatedReportResponse)
def children(status: str | None=None, gender: str | None=None, district: str | None=None,
             province: str | None=None, admission_from: date | None=None, admission_to: date | None=None,
             has_sponsor: bool | None=None, has_bed: bool | None=None,
             has_medical_profile: bool | None=None, has_case_profile: bool | None=None,
             risk_level: str | None=None, welfare_status: str | None=None,
             p: tuple=Depends(paging), db: Session=Depends(get_db), user: User=Depends(can_operational_read)):
    return report_service.children_report(db, user.username, limit=p[0], offset=p[1], status=status, gender=gender, district=district, province=province, admission_from=admission_from, admission_to=admission_to, has_sponsor=has_sponsor, has_bed=has_bed, has_medical_profile=has_medical_profile, has_case_profile=has_case_profile, risk_level=risk_level, welfare_status=welfare_status)

@router.get("/consolidated/sponsorships", response_model=ConsolidatedReportResponse)
def sponsorships(sponsor_status: str | None=None, sponsorship_status: str | None=None,
                 sponsorship_type: str | None=None, start_from: date | None=None,
                 start_to: date | None=None, end_from: date | None=None, end_to: date | None=None,
                 expiring_within_days: int | None=Query(None, ge=0, le=3650),
                 p: tuple=Depends(paging), db: Session=Depends(get_db), user: User=Depends(can_operational_read)):
    return report_service.sponsorships_report(db, user.username, limit=p[0], offset=p[1], sponsor_status=sponsor_status, sponsorship_status=sponsorship_status, sponsorship_type=sponsorship_type, start_from=start_from, start_to=start_to, end_from=end_from, end_to=end_to, expiring_within_days=expiring_within_days)

@router.get("/consolidated/accommodation", response_model=ConsolidatedReportResponse)
def accommodation(building_id: int | None=None, block_id: int | None=None, floor_id: int | None=None,
                  room_id: int | None=None, bed_status: str | None=None,
                  p: tuple=Depends(paging), db: Session=Depends(get_db), user: User=Depends(can_operational_read)):
    return report_service.accommodation_report(db, user.username, limit=p[0], offset=p[1], building_id=building_id, block_id=block_id, floor_id=floor_id, room_id=room_id, bed_status=bed_status)

@router.get("/consolidated/medical", response_model=ConsolidatedReportResponse)
def medical(has_medical_profile: bool | None=None, has_active_medication: bool | None=None,
            has_upcoming_vaccination: bool | None=None, has_special_needs: bool | None=None,
            has_chronic_disease: bool | None=None, p: tuple=Depends(paging),
            db: Session=Depends(get_db), user: User=Depends(can_operational_read)):
    return report_service.medical_report(db, user.username, limit=p[0], offset=p[1], has_medical_profile=has_medical_profile, has_active_medication=has_active_medication, has_upcoming_vaccination=has_upcoming_vaccination, has_special_needs=has_special_needs, has_chronic_disease=has_chronic_disease)

@router.get("/consolidated/education", response_model=ConsolidatedReportResponse)
def education(school_id: int | None=None, class_level: str | None=None, academic_year: str | None=None,
              active_only: bool | None=None, low_attendance_below: float | None=None,
              marks_below: float | None=None, marks_above: float | None=None,
              p: tuple=Depends(paging), db: Session=Depends(get_db), user: User=Depends(can_operational_read)):
    return report_service.education_report(db, user.username, limit=p[0], offset=p[1], school_id=school_id, class_level=class_level, academic_year=academic_year, active_only=active_only, low_attendance_below=low_attendance_below, marks_below=marks_below, marks_above=marks_above)

@router.get("/consolidated/case-management", response_model=ConsolidatedReportResponse)
def cases(case_status: str | None=None, risk_level: str | None=None, welfare_status: str | None=None,
          pending_follow_up: bool | None=None, pending_incident_review: bool | None=None,
          has_active_care_plan: bool | None=None, p: tuple=Depends(paging),
          db: Session=Depends(get_db), user: User=Depends(can_operational_read)):
    return report_service.case_report(db, user.username, limit=p[0], offset=p[1], case_status=case_status, risk_level=risk_level, welfare_status=welfare_status, pending_follow_up=pending_follow_up, pending_incident_review=pending_incident_review, has_active_care_plan=has_active_care_plan)

def rankings(db, column):
    return [AuditRanking(key=str(k), count=c) for k,c in db.execute(select(column, func.count()).group_by(column).order_by(func.count().desc()).limit(10))]

@router.get("/audit-summary", response_model=AuditSummaryResponse)
def audit_summary(db: Session=Depends(get_db), _: User=Depends(require_admin)):
    now=datetime.now(timezone.utc).replace(tzinfo=None); month=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    count=lambda *f: db.scalar(select(func.count()).select_from(AuditLog).where(*f)) or 0
    return AuditSummaryResponse(total_audit_logs=count(), logs_today=count(AuditLog.created_at>=datetime.combine(now.date(),datetime.min.time())), logs_this_month=count(AuditLog.created_at>=month), top_actions=rankings(db,AuditLog.action), top_modules=rankings(db,AuditLog.module), top_users_by_activity=rankings(db,AuditLog.user_id))
