from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.accommodation import Bed, BedAllocation, Block, Building, Floor, Room
from app.models.attendance import Attendance
from app.models.case_management import CarePlan, CaseNote, ChildCaseProfile, IncidentRecord
from app.models.child import Child
from app.models.education_record import EducationRecord
from app.models.exam_result import ExamResult
from app.models.medical_profile import MedicalProfile
from app.models.medication import Medication
from app.models.school import School
from app.models.sponsor import ChildSponsorship, Sponsor
from app.models.vaccination import Vaccination
from app.schemas.consolidated_reports import ConsolidatedReportResponse, PaginationInfo


def clean_filters(filters: dict[str, Any]) -> dict[str, Any]:
    return jsonable_encoder({key: value for key, value in filters.items() if value is not None})


def build_report(db: Session, statement, *, limit: int, offset: int, filters: dict, username: str) -> ConsolidatedReportResponse:
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    rows = db.execute(statement.offset(offset).limit(limit)).mappings().all()
    return ConsolidatedReportResponse(
        data=jsonable_encoder([dict(row) for row in rows]),
        pagination=PaginationInfo(limit=limit, offset=offset, total=total),
        filters_applied=clean_filters(filters), generated_at=datetime.now(UTC),
        generated_by=username, export_ready=True,
    )


def children_report(db: Session, username: str, *, limit=50, offset=0, status=None, gender=None,
                    district=None, province=None, admission_from=None, admission_to=None,
                    has_sponsor=None, has_bed=None, has_medical_profile=None, has_case_profile=None,
                    risk_level=None, welfare_status=None):
    today = date.today()
    sponsor_exists = select(ChildSponsorship.id).where(
        ChildSponsorship.child_id == Child.id, ChildSponsorship.status == "Active",
        ChildSponsorship.start_date <= today,
        or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= today),
    ).correlate(Child).exists()
    bed_exists = select(BedAllocation.id).where(BedAllocation.child_id == Child.id, BedAllocation.status == "Active").correlate(Child).exists()
    medical_exists = select(MedicalProfile.id).where(MedicalProfile.child_id == Child.id).correlate(Child).exists()
    case_exists = select(ChildCaseProfile.id).where(ChildCaseProfile.child_id == Child.id, ChildCaseProfile.deleted_at.is_(None)).correlate(Child).exists()
    stmt = select(
        Child.id, Child.child_id, Child.full_name, Child.gender, Child.date_of_birth,
        Child.status, Child.admission_date, Child.district, Child.province,
        sponsor_exists.label("has_active_sponsor"), bed_exists.label("has_active_bed"),
        medical_exists.label("has_medical_profile"), case_exists.label("has_case_profile"),
        ChildCaseProfile.risk_level, ChildCaseProfile.welfare_status,
    ).outerjoin(ChildCaseProfile, (ChildCaseProfile.child_id == Child.id) & ChildCaseProfile.deleted_at.is_(None))
    if status: stmt = stmt.where(Child.status == status)
    if gender: stmt = stmt.where(Child.gender == gender)
    if district: stmt = stmt.where(Child.district.ilike(f"%{district}%"))
    if province: stmt = stmt.where(Child.province.ilike(f"%{province}%"))
    if admission_from: stmt = stmt.where(Child.admission_date >= admission_from)
    if admission_to: stmt = stmt.where(Child.admission_date <= admission_to)
    for value, condition in ((has_sponsor, sponsor_exists), (has_bed, bed_exists),
                             (has_medical_profile, medical_exists), (has_case_profile, case_exists)):
        if value is not None: stmt = stmt.where(condition if value else ~condition)
    if risk_level: stmt = stmt.where(ChildCaseProfile.risk_level == risk_level)
    if welfare_status: stmt = stmt.where(ChildCaseProfile.welfare_status == welfare_status)
    filters = locals().copy(); [filters.pop(k, None) for k in ("db", "username", "stmt", "today", "sponsor_exists", "bed_exists", "medical_exists", "case_exists", "condition", "value")]
    return build_report(db, stmt.order_by(Child.full_name), limit=limit, offset=offset, filters=filters, username=username)


def sponsors_report(db: Session, username: str, *, limit=500, offset=0, sponsor_status=None):
    stmt = select(Sponsor.id, Sponsor.sponsor_code, Sponsor.sponsor_type, Sponsor.full_name,
                  Sponsor.organization_name, Sponsor.city, Sponsor.district, Sponsor.province,
                  Sponsor.country, Sponsor.status).where(Sponsor.deleted_at.is_(None))
    if sponsor_status: stmt = stmt.where(Sponsor.status == sponsor_status)
    return build_report(db, stmt.order_by(Sponsor.sponsor_code), limit=limit, offset=offset,
                        filters={"sponsor_status": sponsor_status}, username=username)


def sponsorships_report(db: Session, username: str, *, limit=50, offset=0, sponsor_status=None,
                        sponsorship_status=None, sponsorship_type=None, start_from=None,
                        start_to=None, end_from=None, end_to=None, expiring_within_days=None):
    stmt = select(
        ChildSponsorship.id, ChildSponsorship.child_id, ChildSponsorship.sponsor_id,
        Sponsor.sponsor_code, Sponsor.full_name.label("sponsor_name"), Sponsor.status.label("sponsor_status"),
        ChildSponsorship.sponsorship_type, ChildSponsorship.status.label("sponsorship_status"),
        ChildSponsorship.start_date, ChildSponsorship.end_date,
    ).join(Sponsor, Sponsor.id == ChildSponsorship.sponsor_id).where(Sponsor.deleted_at.is_(None))
    if sponsor_status: stmt = stmt.where(Sponsor.status == sponsor_status)
    if sponsorship_status: stmt = stmt.where(ChildSponsorship.status == sponsorship_status)
    if sponsorship_type: stmt = stmt.where(ChildSponsorship.sponsorship_type == sponsorship_type)
    if start_from: stmt = stmt.where(ChildSponsorship.start_date >= start_from)
    if start_to: stmt = stmt.where(ChildSponsorship.start_date <= start_to)
    if end_from: stmt = stmt.where(ChildSponsorship.end_date >= end_from)
    if end_to: stmt = stmt.where(ChildSponsorship.end_date <= end_to)
    if expiring_within_days is not None:
        stmt = stmt.where(ChildSponsorship.end_date.between(date.today(), date.today() + timedelta(days=expiring_within_days)))
    filters = {k: v for k, v in locals().items() if k not in {"db", "username", "stmt"}}
    return build_report(db, stmt.order_by(ChildSponsorship.start_date.desc()), limit=limit, offset=offset, filters=filters, username=username)


def accommodation_report(db: Session, username: str, *, limit=50, offset=0, building_id=None,
                         block_id=None, floor_id=None, room_id=None, bed_status=None):
    stmt = select(
        Bed.id, Bed.bed_code, Bed.bed_name, Bed.status.label("bed_status"), Room.id.label("room_id"),
        Room.room_code, Room.room_name, Floor.id.label("floor_id"), Floor.floor_no, Floor.floor_name,
        Block.id.label("block_id"), Block.block_code, Block.block_name,
        Building.id.label("building_id"), Building.building_code, Building.building_name,
    ).join(Room, Room.id == Bed.room_id).join(Floor, Floor.id == Room.floor_id).join(Block, Block.id == Floor.block_id).join(Building, Building.id == Block.building_id).where(
        Bed.deleted_at.is_(None), Room.deleted_at.is_(None), Floor.deleted_at.is_(None),
        Block.deleted_at.is_(None), Building.deleted_at.is_(None),
    )
    if building_id: stmt = stmt.where(Building.id == building_id)
    if block_id: stmt = stmt.where(Block.id == block_id)
    if floor_id: stmt = stmt.where(Floor.id == floor_id)
    if room_id: stmt = stmt.where(Room.id == room_id)
    if bed_status: stmt = stmt.where(Bed.status == bed_status)
    return build_report(db, stmt.order_by(Building.building_code, Room.room_code, Bed.bed_code), limit=limit, offset=offset,
                        filters={"building_id": building_id, "block_id": block_id, "floor_id": floor_id, "room_id": room_id, "bed_status": bed_status}, username=username)


def medical_report(db: Session, username: str, *, limit=50, offset=0, has_medical_profile=None,
                   has_active_medication=None, has_upcoming_vaccination=None,
                   has_special_needs=None, has_chronic_disease=None):
    today = date.today()
    profile_exists = select(MedicalProfile.id).where(MedicalProfile.child_id == Child.id).correlate(Child).exists()
    medication_exists = select(Medication.id).where(Medication.child_id == Child.id, Medication.status == "Active").correlate(Child).exists()
    vaccination_exists = select(Vaccination.id).where(Vaccination.child_id == Child.id, Vaccination.next_due_date.between(today, today + timedelta(days=30))).correlate(Child).exists()
    special = select(MedicalProfile.id).where(MedicalProfile.child_id == Child.id, MedicalProfile.special_needs.is_not(None), func.trim(MedicalProfile.special_needs) != "").correlate(Child).exists()
    chronic = select(MedicalProfile.id).where(MedicalProfile.child_id == Child.id, MedicalProfile.chronic_diseases.is_not(None), func.trim(MedicalProfile.chronic_diseases) != "").correlate(Child).exists()
    stmt = select(Child.id, Child.child_id, Child.full_name, Child.status,
                  profile_exists.label("has_medical_profile"), medication_exists.label("has_active_medication"),
                  vaccination_exists.label("has_upcoming_vaccination"), special.label("has_special_needs"), chronic.label("has_chronic_disease"))
    for value, condition in ((has_medical_profile, profile_exists), (has_active_medication, medication_exists),
                             (has_upcoming_vaccination, vaccination_exists), (has_special_needs, special),
                             (has_chronic_disease, chronic)):
        if value is not None: stmt = stmt.where(condition if value else ~condition)
    filters = {k: v for k, v in locals().items() if k not in {"db", "username", "stmt", "today", "profile_exists", "medication_exists", "vaccination_exists", "special", "chronic", "value", "condition"}}
    return build_report(db, stmt.order_by(Child.full_name), limit=limit, offset=offset, filters=filters, username=username)


def education_report(db: Session, username: str, *, limit=50, offset=0, school_id=None,
                     class_level=None, academic_year=None, active_only=None,
                     low_attendance_below=None, marks_below=None, marks_above=None):
    attendance_sub = select(Attendance.attendance_percentage).where(Attendance.education_record_id == EducationRecord.id).order_by(Attendance.year.desc(), Attendance.month.desc()).limit(1).scalar_subquery()
    marks_sub = select(ExamResult.percentage).where(ExamResult.education_record_id == EducationRecord.id).order_by(ExamResult.exam_date.desc()).limit(1).scalar_subquery()
    stmt = select(EducationRecord.id, EducationRecord.child_id, School.school_code, School.school_name,
                  EducationRecord.class_level, EducationRecord.academic_year, EducationRecord.status,
                  attendance_sub.label("latest_attendance_percentage"), marks_sub.label("latest_exam_percentage")).join(School, School.id == EducationRecord.school_id)
    if school_id: stmt = stmt.where(School.id == school_id)
    if class_level: stmt = stmt.where(EducationRecord.class_level == class_level)
    if academic_year: stmt = stmt.where(EducationRecord.academic_year == academic_year)
    if active_only is True: stmt = stmt.where(EducationRecord.status == "Studying")
    if active_only is False: stmt = stmt.where(EducationRecord.status != "Studying")
    if low_attendance_below is not None: stmt = stmt.where(attendance_sub < low_attendance_below)
    if marks_below is not None: stmt = stmt.where(marks_sub < marks_below)
    if marks_above is not None: stmt = stmt.where(marks_sub > marks_above)
    return build_report(db, stmt.order_by(EducationRecord.start_date.desc()), limit=limit, offset=offset,
        filters={"school_id": school_id, "class_level": class_level, "academic_year": academic_year, "active_only": active_only,
                 "low_attendance_below": low_attendance_below, "marks_below": marks_below, "marks_above": marks_above}, username=username)


def case_report(db: Session, username: str, *, limit=50, offset=0, case_status=None,
                risk_level=None, welfare_status=None, pending_follow_up=None,
                pending_incident_review=None, has_active_care_plan=None):
    follow_exists = select(CaseNote.id).where(CaseNote.child_id == ChildCaseProfile.child_id, CaseNote.deleted_at.is_(None), CaseNote.follow_up_required.is_(True), CaseNote.follow_up_date <= date.today()).exists()
    incident_exists = select(IncidentRecord.id).where(IncidentRecord.child_id == ChildCaseProfile.child_id, IncidentRecord.deleted_at.is_(None), IncidentRecord.review_status == "Pending Review").exists()
    plan_exists = select(CarePlan.id).where(CarePlan.child_id == ChildCaseProfile.child_id, CarePlan.deleted_at.is_(None), CarePlan.status == "Active").exists()
    stmt = select(ChildCaseProfile.id, ChildCaseProfile.child_id, ChildCaseProfile.case_number,
                  ChildCaseProfile.case_status, ChildCaseProfile.risk_level, ChildCaseProfile.welfare_status,
                  ChildCaseProfile.assigned_case_worker, follow_exists.label("pending_follow_up"),
                  incident_exists.label("pending_incident_review"), plan_exists.label("has_active_care_plan")).where(ChildCaseProfile.deleted_at.is_(None))
    if case_status: stmt = stmt.where(ChildCaseProfile.case_status == case_status)
    if risk_level: stmt = stmt.where(ChildCaseProfile.risk_level == risk_level)
    if welfare_status: stmt = stmt.where(ChildCaseProfile.welfare_status == welfare_status)
    for value, condition in ((pending_follow_up, follow_exists), (pending_incident_review, incident_exists), (has_active_care_plan, plan_exists)):
        if value is not None: stmt = stmt.where(condition if value else ~condition)
    return build_report(db, stmt.order_by(ChildCaseProfile.case_number), limit=limit, offset=offset,
        filters={"case_status": case_status, "risk_level": risk_level, "welfare_status": welfare_status,
                 "pending_follow_up": pending_follow_up, "pending_incident_review": pending_incident_review,
                 "has_active_care_plan": has_active_care_plan}, username=username)
