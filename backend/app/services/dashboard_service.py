from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import Integer, cast, func, not_, or_, select
from sqlalchemy.orm import Session

from app.models.accommodation import Bed, BedAllocation, Block, Building, Floor, Room
from app.models.attendance import Attendance
from app.models.case_management import CarePlan, CaseNote, CaseReview, ChildCaseProfile, CounselingSession, IncidentRecord
from app.models.child import Child
from app.models.document import Document
from app.models.education_record import EducationRecord
from app.models.exam_result import ExamResult
from app.models.medical_profile import MedicalProfile
from app.models.medical_visit import MedicalVisit
from app.models.medication import Medication
from app.models.school import School
from app.models.sponsor import ChildSponsorship, Sponsor
from app.models.vaccination import Vaccination
from app.models.child_attendance import DailyChildAttendance
from app.schemas.dashboard import (
    AccommodationSummary, AlertGroup, AlertsDashboardResponse, AlertsSummary,
    CaseManagementSummary, ChildCompleteProfileSummaryResponse, ChildrenSummary,
    DocumentSummary, EducationSummary, ExecutiveDashboardResponse, GlobalSearchResponse,
    MedicalSummary, OperationalDashboardResponse, PendingActionsSummary,
    SafeAlertReference, SearchResult, SponsorshipSummary,
)

REQUIRED_DOCUMENT_TYPES = {
    "Admission Form", "Affidavit", "Death Certificate", "Father CNIC",
    "Guardian CNIC", "Birth Certificate", "Child Photo",
}


def windows() -> dict[str, date]:
    today = date.today()
    return {
        "today": today,
        "week_start": today - timedelta(days=today.weekday()),
        "month_start": today.replace(day=1),
        "next_30": today + timedelta(days=30),
    }


def scalar(db: Session, statement) -> int:
    return db.scalar(statement) or 0


def count_model(db: Session, model, *filters) -> int:
    return scalar(db, select(func.count()).select_from(model).where(*filters))


def exists_for(model, child_column, *filters):
    return select(model.id).where(child_column == Child.id, *filters).exists()


def summary_counts(db: Session) -> dict:
    w = windows(); today = w["today"]
    active_sponsorship = exists_for(
        ChildSponsorship, ChildSponsorship.child_id,
        ChildSponsorship.status == "Active", ChildSponsorship.start_date <= today,
        or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= today),
    )
    active_bed = exists_for(BedAllocation, BedAllocation.child_id, BedAllocation.status == "Active")
    medical_profile = exists_for(MedicalProfile, MedicalProfile.child_id)
    education_record = exists_for(EducationRecord, EducationRecord.child_id, EducationRecord.status == "Studying")
    case_profile = exists_for(ChildCaseProfile, ChildCaseProfile.child_id, ChildCaseProfile.deleted_at.is_(None))

    total_children = count_model(db, Child)
    without_sponsor = count_model(db, Child, not_(active_sponsorship))
    without_bed = count_model(db, Child, not_(active_bed))
    without_medical = count_model(db, Child, not_(medical_profile))
    without_education = count_model(db, Child, not_(education_record))
    without_case = count_model(db, Child, not_(case_profile))
    active_sponsorships = count_model(
        db, ChildSponsorship, ChildSponsorship.status == "Active",
        ChildSponsorship.start_date <= today,
        or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= today),
    )
    expiring_sponsorships = count_model(
        db, ChildSponsorship, ChildSponsorship.status == "Active",
        ChildSponsorship.end_date.between(today, w["next_30"]),
    )
    bed_counts = dict(db.execute(
        select(Bed.status, func.count(Bed.id)).where(Bed.deleted_at.is_(None)).group_by(Bed.status)
    ).all())
    total_beds = sum(bed_counts.values()); occupied = bed_counts.get("Occupied", 0)
    upcoming_vaccinations = count_model(db, Vaccination, Vaccination.next_due_date.between(today, w["next_30"]))
    active_medications = count_model(db, Medication, Medication.status == "Active")
    pending_followups = count_model(
        db, CaseNote, CaseNote.deleted_at.is_(None), CaseNote.follow_up_required.is_(True),
        CaseNote.follow_up_date <= today,
    )
    upcoming_reviews = count_model(
        db, CaseReview, CaseReview.deleted_at.is_(None),
        or_(CaseReview.next_review_date.between(today, w["next_30"]),
            (CaseReview.status == "Pending") & CaseReview.review_date.between(today, w["next_30"])),
    )
    upcoming_counseling = count_model(
        db, CounselingSession, CounselingSession.deleted_at.is_(None),
        or_(CounselingSession.next_session_date.between(today, w["next_30"]),
            (CounselingSession.status == "Scheduled") & CounselingSession.session_date.between(today, w["next_30"])),
    )
    pending_incidents = count_model(db, IncidentRecord, IncidentRecord.deleted_at.is_(None), IncidentRecord.review_status == "Pending Review")
    active_plans = count_model(db, CarePlan, CarePlan.deleted_at.is_(None), CarePlan.status == "Active")
    critical_incidents = count_model(db, IncidentRecord, IncidentRecord.deleted_at.is_(None), IncidentRecord.severity == "Critical", IncidentRecord.review_status != "Closed")
    complete_doc_subquery = (
        select(Document.child_id).where(Document.document_type.in_(REQUIRED_DOCUMENT_TYPES))
        .group_by(Document.child_id).having(func.count(func.distinct(Document.document_type)) >= len(REQUIRED_DOCUMENT_TYPES))
    ).subquery()
    complete_documents = scalar(db, select(func.count()).select_from(complete_doc_subquery))

    return {
        "windows": w, "total_children": total_children,
        "without_sponsor": without_sponsor, "without_bed": without_bed,
        "without_medical": without_medical, "without_education": without_education,
        "without_case": without_case, "active_sponsorships": active_sponsorships,
        "expiring_sponsorships": expiring_sponsorships, "bed_counts": bed_counts,
        "total_beds": total_beds, "occupied": occupied,
        "upcoming_vaccinations": upcoming_vaccinations, "active_medications": active_medications,
        "pending_followups": pending_followups, "upcoming_reviews": upcoming_reviews,
        "upcoming_counseling": upcoming_counseling, "pending_incidents": pending_incidents,
        "active_plans": active_plans, "critical_incidents": critical_incidents,
        "complete_documents": complete_documents,
    }


def executive_dashboard(db: Session) -> ExecutiveDashboardResponse:
    c = summary_counts(db); w = c["windows"]; today = w["today"]
    total_children = c["total_children"]
    total_sponsors = count_model(db, Sponsor, Sponsor.deleted_at.is_(None))
    active_sponsors = count_model(db, Sponsor, Sponsor.deleted_at.is_(None), Sponsor.status == "Active")
    total_docs = count_model(db, Document); verified = count_model(db, Document, Document.is_verified.is_(True))
    special_needs = count_model(db, MedicalProfile, MedicalProfile.special_needs.is_not(None), func.trim(MedicalProfile.special_needs) != "")
    chronic = count_model(db, MedicalProfile, MedicalProfile.chronic_diseases.is_not(None), func.trim(MedicalProfile.chronic_diseases) != "")
    month_end = (w["month_start"].replace(day=28) + timedelta(days=4)).replace(day=1)
    average_attendance = float(db.scalar(select(func.avg(Attendance.attendance_percentage))) or 0)
    average_marks = float(db.scalar(select(func.avg(ExamResult.percentage))) or 0)
    critical_risk = count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.risk_level == "Critical")
    high_risk = count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.risk_level == "High")
    case_profiles = count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None))
    open_cases = count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.case_status.in_(["Open", "Under Review"]))
    return ExecutiveDashboardResponse(
        children_summary=ChildrenSummary(
            total_children=total_children,
            active_children=count_model(db, Child, Child.status == "Active"),
            inactive_children=count_model(db, Child, Child.status == "Inactive"),
            discharged_children=count_model(db, Child, Child.status == "Discharged"),
            transferred_children=count_model(db, Child, Child.status == "Transferred"),
            children_admitted_today=count_model(db, Child, Child.admission_date == today),
            children_admitted_this_week=count_model(db, Child, Child.admission_date.between(w["week_start"], today)),
            children_admitted_this_month=count_model(db, Child, Child.admission_date.between(w["month_start"], today)),
            children_without_case_profile=c["without_case"], children_without_medical_profile=c["without_medical"],
            children_without_education_record=c["without_education"], children_without_bed=c["without_bed"],
            children_without_active_sponsor=c["without_sponsor"],
        ),
        sponsorship_summary=SponsorshipSummary(
            total_sponsors=total_sponsors, active_sponsors=active_sponsors,
            inactive_sponsors=total_sponsors - active_sponsors,
            active_sponsorships=c["active_sponsorships"],
            expired_sponsorships=count_model(db, ChildSponsorship, ChildSponsorship.end_date < today),
            sponsorships_expiring_30_days=c["expiring_sponsorships"],
            children_with_active_sponsor=total_children - c["without_sponsor"],
            children_without_active_sponsor=c["without_sponsor"],
        ),
        accommodation_summary=AccommodationSummary(
            total_buildings=count_model(db, Building, Building.deleted_at.is_(None)),
            total_blocks=count_model(db, Block, Block.deleted_at.is_(None)),
            total_floors=count_model(db, Floor, Floor.deleted_at.is_(None)),
            total_rooms=count_model(db, Room, Room.deleted_at.is_(None)), total_beds=c["total_beds"],
            occupied_beds=c["occupied"], vacant_beds=c["bed_counts"].get("Vacant", 0),
            reserved_beds=c["bed_counts"].get("Reserved", 0), maintenance_beds=c["bed_counts"].get("Maintenance", 0),
            occupancy_percentage=round(c["occupied"] * 100 / c["total_beds"], 2) if c["total_beds"] else 0,
        ),
        medical_summary=MedicalSummary(
            children_with_medical_profiles=total_children - c["without_medical"], children_without_medical_profile=c["without_medical"],
            active_medications=c["active_medications"], upcoming_vaccinations_30_days=c["upcoming_vaccinations"],
            medical_visits_this_month=count_model(db, MedicalVisit, MedicalVisit.visit_date >= w["month_start"], MedicalVisit.visit_date < month_end),
            children_with_special_needs=special_needs, children_with_chronic_diseases=chronic,
        ),
        education_summary=EducationSummary(
            active_students=count_model(db, EducationRecord, EducationRecord.status == "Studying"),
            schools_count=count_model(db, School, School.status == "Active"),
            average_attendance=round(average_attendance, 2), average_marks=round(average_marks, 2),
            board_exam_students=scalar(db, select(func.count(func.distinct(EducationRecord.child_id))).select_from(EducationRecord).join(ExamResult, ExamResult.education_record_id == EducationRecord.id).where(ExamResult.exam_name == "Board")),
            low_attendance_students=scalar(db, select(func.count(func.distinct(EducationRecord.child_id))).select_from(EducationRecord).join(Attendance, Attendance.education_record_id == EducationRecord.id).where(Attendance.attendance_percentage < 75)),
            dropout_students=scalar(db, select(func.count(func.distinct(EducationRecord.child_id))).where(EducationRecord.status == "Dropped")),
        ),
        case_management_summary=CaseManagementSummary(
            total_case_profiles=case_profiles, open_cases=open_cases,
            closed_cases=count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.case_status == "Closed"),
            high_risk_children=high_risk, critical_risk_children=critical_risk,
            pending_follow_ups=c["pending_followups"], upcoming_case_reviews_30_days=c["upcoming_reviews"],
            upcoming_counseling_sessions_30_days=c["upcoming_counseling"], critical_incidents=c["critical_incidents"],
            pending_incident_reviews=c["pending_incidents"], active_care_plans=c["active_plans"],
        ),
        document_summary=DocumentSummary(
            total_documents=total_docs, verified_documents=verified, unverified_documents=total_docs - verified,
            children_with_complete_admission_documents=c["complete_documents"],
            children_with_incomplete_admission_documents=max(total_children - c["complete_documents"], 0),
        ),
        alerts_summary=AlertsSummary(
            critical_incidents=c["critical_incidents"], critical_risk_children=critical_risk,
            upcoming_vaccinations=c["upcoming_vaccinations"], active_medications=c["active_medications"],
            pending_follow_ups=c["pending_followups"], pending_incident_reviews=c["pending_incidents"],
            children_without_beds=c["without_bed"], children_without_active_sponsors=c["without_sponsor"],
            children_without_medical_profiles=c["without_medical"], children_without_case_profiles=c["without_case"],
        ),
        pending_actions_summary=PendingActionsSummary(
            documents_pending_verification=total_docs - verified, incidents_pending_review=c["pending_incidents"],
            follow_ups_due=c["pending_followups"], case_reviews_due=c["upcoming_reviews"],
            vaccinations_due=c["upcoming_vaccinations"], children_pending_bed_allocation=c["without_bed"],
            children_pending_sponsorship=c["without_sponsor"],
        ),
    )


def operational_dashboard(db: Session) -> OperationalDashboardResponse:
    c = summary_counts(db); w = c["windows"]; today = w["today"]
    total_docs = count_model(db, Document); verified = count_model(db, Document, Document.is_verified.is_(True))
    low_attendance = scalar(db, select(func.count(func.distinct(EducationRecord.child_id))).select_from(EducationRecord).join(Attendance, Attendance.education_record_id == EducationRecord.id).where(Attendance.attendance_percentage < 75))
    return OperationalDashboardResponse(
        today_admissions=count_model(db, Child, Child.admission_date == today),
        this_week_admissions=count_model(db, Child, Child.admission_date.between(w["week_start"], today)),
        this_month_admissions=count_model(db, Child, Child.admission_date.between(w["month_start"], today)),
        pending_document_verifications=total_docs - verified,
        vacant_beds=c["bed_counts"].get("Vacant", 0), occupied_beds=c["occupied"],
        children_without_beds=c["without_bed"], active_sponsorships=c["active_sponsorships"],
        expiring_sponsorships_30_days=c["expiring_sponsorships"], upcoming_vaccinations_30_days=c["upcoming_vaccinations"],
        upcoming_case_reviews_30_days=c["upcoming_reviews"], upcoming_counseling_sessions_30_days=c["upcoming_counseling"],
        active_medications=c["active_medications"], pending_incident_reviews=c["pending_incidents"],
        follow_ups_due=c["pending_followups"], low_attendance_children=low_attendance,
        children_with_active_care_plans=scalar(db, select(func.count(func.distinct(CarePlan.child_id))).where(CarePlan.deleted_at.is_(None), CarePlan.status == "Active")),
    )


def alert_references(db: Session, detailed: bool) -> AlertsDashboardResponse:
    c = summary_counts(db); counts_critical = {
        "critical_incidents": c["critical_incidents"],
        "critical_risk_children": count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.risk_level == "Critical"),
        "children_with_critical_welfare_status": count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.welfare_status == "Critical"),
        "children_missing_today": count_model(db, DailyChildAttendance, DailyChildAttendance.attendance_date == date.today(), DailyChildAttendance.status == "Missing", DailyChildAttendance.deleted_at.is_(None)),
    }
    warning = {
        "high_risk_children": count_model(db, ChildCaseProfile, ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.risk_level == "High"),
        "upcoming_vaccinations": c["upcoming_vaccinations"], "active_medications": c["active_medications"],
        "children_without_beds": c["without_bed"], "children_without_sponsors": c["without_sponsor"],
        "pending_follow_ups": c["pending_followups"], "pending_incident_reviews": c["pending_incidents"],
        "unauthorized_absences_today": count_model(db, DailyChildAttendance, DailyChildAttendance.attendance_date == date.today(), DailyChildAttendance.status == "Unauthorized Absence", DailyChildAttendance.deleted_at.is_(None)),
    }
    info = {"upcoming_case_reviews": c["upcoming_reviews"], "upcoming_counseling_sessions": c["upcoming_counseling"],
            "expiring_sponsorships": c["expiring_sponsorships"],
            "incomplete_documents": c["total_children"] - c["complete_documents"]}
    refs: dict[str, list[SafeAlertReference]] = {}
    if detailed:
        refs["critical_incidents"] = [SafeAlertReference(module="incident", id=r.id, child_id=r.child_id, display_title="Critical incident", status=r.review_status) for r in db.scalars(select(IncidentRecord).where(IncidentRecord.deleted_at.is_(None), IncidentRecord.severity == "Critical", IncidentRecord.review_status != "Closed").limit(25))]
        refs["critical_risk_children"] = [SafeAlertReference(module="case", id=r.id, child_id=r.child_id, display_title=r.case_number, status=r.risk_level) for r in db.scalars(select(ChildCaseProfile).where(ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.risk_level == "Critical").limit(25))]
    return AlertsDashboardResponse(
        critical_alerts=AlertGroup(counts=counts_critical, references=refs),
        warning_alerts=AlertGroup(counts=warning), info_alerts=AlertGroup(counts=info),
    )


def child_complete_profile(db: Session, child_id: int) -> ChildCompleteProfileSummaryResponse:
    child = db.get(Child, child_id)
    if child is None: raise HTTPException(status_code=404, detail="Child not found")
    today = date.today(); age = today.year - child.date_of_birth.year - ((today.month, today.day) < (child.date_of_birth.month, child.date_of_birth.day))
    docs = db.execute(select(func.count(Document.id), func.sum(cast(Document.is_verified, Integer)), func.count(func.distinct(Document.document_type))).where(Document.child_id == child_id)).one()
    sponsorships = db.execute(select(ChildSponsorship.sponsorship_type, func.count()).where(ChildSponsorship.child_id == child_id, ChildSponsorship.status == "Active", ChildSponsorship.start_date <= today, or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= today)).group_by(ChildSponsorship.sponsorship_type)).all()
    bed_row = db.execute(select(BedAllocation, Bed, Room, Floor, Block, Building).join(Bed, Bed.id == BedAllocation.bed_id).join(Room, Room.id == Bed.room_id).join(Floor, Floor.id == Room.floor_id).join(Block, Block.id == Floor.block_id).join(Building, Building.id == Block.building_id).where(BedAllocation.child_id == child_id, BedAllocation.status == "Active")).first()
    medical = db.scalar(select(MedicalProfile).where(MedicalProfile.child_id == child_id))
    education = db.execute(select(EducationRecord, School).join(School, School.id == EducationRecord.school_id).where(EducationRecord.child_id == child_id, EducationRecord.status == "Studying")).first()
    profile = db.scalar(select(ChildCaseProfile).where(ChildCaseProfile.child_id == child_id, ChildCaseProfile.deleted_at.is_(None)))
    latest_attendance = db.scalar(select(Attendance.attendance_percentage).join(EducationRecord, EducationRecord.id == Attendance.education_record_id).where(EducationRecord.child_id == child_id).order_by(Attendance.year.desc(), Attendance.month.desc()).limit(1))
    latest_exam = db.scalar(select(ExamResult.percentage).join(EducationRecord, EducationRecord.id == ExamResult.education_record_id).where(EducationRecord.child_id == child_id).order_by(ExamResult.exam_date.desc()).limit(1))
    month_start = today.replace(day=1)
    attendance_rows = db.execute(select(DailyChildAttendance.status, func.count()).where(DailyChildAttendance.child_id == child_id, DailyChildAttendance.deleted_at.is_(None), DailyChildAttendance.attendance_date.between(month_start, today)).group_by(DailyChildAttendance.status)).all()
    attendance_counts = dict(attendance_rows)
    attendance_total = sum(attendance_counts.values())
    present_count = attendance_counts.get("Present", 0)
    absent_count = attendance_counts.get("Absent", 0) + attendance_counts.get("Unauthorized Absence", 0) + attendance_counts.get("Missing", 0)
    leave_count = attendance_counts.get("On Leave", 0) + attendance_counts.get("Medical Leave", 0)
    today_attendance = db.scalar(select(DailyChildAttendance.status).where(DailyChildAttendance.child_id == child_id, DailyChildAttendance.attendance_date == today, DailyChildAttendance.deleted_at.is_(None)))
    return ChildCompleteProfileSummaryResponse(
        child_basic={"id": child.id, "child_id": child.child_id, "admission_file_no": child.admission_file_no, "full_name": child.full_name, "gender": child.gender, "date_of_birth": child.date_of_birth, "age": age, "district": child.district, "province": child.province, "status": child.status, "admission_date": child.admission_date},
        admission_documents={"required_documents_count": len(REQUIRED_DOCUMENT_TYPES), "uploaded_documents_count": docs[0] or 0, "verified_documents_count": int(docs[1] or 0), "pending_verification_count": (docs[0] or 0) - int(docs[1] or 0), "admission_complete": (docs[2] or 0) >= len(REQUIRED_DOCUMENT_TYPES)},
        sponsorship={"has_active_sponsor": bool(sponsorships), "active_sponsor_count": sum(r[1] for r in sponsorships), "current_sponsorship_types": [r[0] for r in sponsorships]},
        accommodation={"has_active_bed": bool(bed_row), "building": bed_row[5].building_name if bed_row else None, "block": bed_row[4].block_name if bed_row else None, "floor": bed_row[3].floor_name if bed_row else None, "room": bed_row[2].room_name if bed_row else None, "bed": bed_row[1].bed_name if bed_row else None, "allocation_date": bed_row[0].allocation_date if bed_row else None, "bed_status": bed_row[1].status if bed_row else None},
        medical={"has_medical_profile": medical is not None, "blood_group": medical.blood_group if medical else None, "active_medication_count": count_model(db, Medication, Medication.child_id == child_id, Medication.status == "Active"), "upcoming_vaccination_count": count_model(db, Vaccination, Vaccination.child_id == child_id, Vaccination.next_due_date.between(today, today + timedelta(days=30))), "special_needs_flag": bool(medical and medical.special_needs and medical.special_needs.strip()), "chronic_disease_flag": bool(medical and medical.chronic_diseases and medical.chronic_diseases.strip())},
        education={"has_active_education_record": bool(education), "current_education_status": education[0].status if education else "Not enrolled", "school_name": education[1].school_name if education else None, "class_level": education[0].class_level if education else None, "academic_year": education[0].academic_year if education else None, "latest_attendance_percentage": float(latest_attendance) if latest_attendance is not None else None, "latest_exam_percentage": float(latest_exam) if latest_exam is not None else None},
        case_management={"has_case_profile": profile is not None, "case_status": profile.case_status if profile else None, "risk_level": profile.risk_level if profile else None, "welfare_status": profile.welfare_status if profile else None, "pending_follow_up_count": count_model(db, CaseNote, CaseNote.child_id == child_id, CaseNote.deleted_at.is_(None), CaseNote.follow_up_required.is_(True), CaseNote.follow_up_date <= today), "active_care_plan_count": count_model(db, CarePlan, CarePlan.child_id == child_id, CarePlan.deleted_at.is_(None), CarePlan.status == "Active"), "critical_incident_count": count_model(db, IncidentRecord, IncidentRecord.child_id == child_id, IncidentRecord.deleted_at.is_(None), IncidentRecord.severity == "Critical", IncidentRecord.review_status != "Closed")},
        daily_attendance={"today_status": today_attendance or "Not marked", "month_present": present_count, "month_absent": absent_count, "month_leave": leave_count, "month_attendance_percentage": round(present_count * 100 / attendance_total, 2) if attendance_total else None},
    )


def global_search(db: Session, q: str, module: str | None, limit: int) -> GlobalSearchResponse:
    pattern = f"%{q.strip()}%"; empty: list[SearchResult] = []
    include = lambda name: module is None or module == name
    children = [SearchResult(module="children", id=r.id, display_title=r.full_name, display_subtitle=r.child_id, status=r.status) for r in db.scalars(select(Child).where(or_(Child.full_name.ilike(pattern), Child.child_id.ilike(pattern), Child.admission_file_no.ilike(pattern))).limit(limit))] if include("children") else empty
    sponsors = [SearchResult(module="sponsors", id=r.id, display_title=r.full_name, display_subtitle=r.sponsor_code, status=r.status) for r in db.scalars(select(Sponsor).where(Sponsor.deleted_at.is_(None), or_(Sponsor.full_name.ilike(pattern), Sponsor.organization_name.ilike(pattern), Sponsor.sponsor_code.ilike(pattern))).limit(limit))] if include("sponsors") else empty
    education = [SearchResult(module="education", id=r.id, display_title=r.school_name, display_subtitle=r.school_code, status=r.status) for r in db.scalars(select(School).where(or_(School.school_name.ilike(pattern), School.school_code.ilike(pattern))).limit(limit))] if include("education") else empty
    accommodation: list[SearchResult] = []
    if include("accommodation"):
        accommodation += [SearchResult(module="building", id=r.id, display_title=r.building_name, display_subtitle=r.building_code, status=r.status) for r in db.scalars(select(Building).where(Building.deleted_at.is_(None), or_(Building.building_name.ilike(pattern), Building.building_code.ilike(pattern))).limit(limit))]
        accommodation += [SearchResult(module="room", id=r.id, display_title=r.room_name, display_subtitle=r.room_code, status=r.status) for r in db.scalars(select(Room).where(Room.deleted_at.is_(None), or_(Room.room_name.ilike(pattern), Room.room_code.ilike(pattern))).limit(limit))]
        accommodation += [SearchResult(module="bed", id=r.id, display_title=r.bed_name, display_subtitle=r.bed_code, status=r.status) for r in db.scalars(select(Bed).where(Bed.deleted_at.is_(None), or_(Bed.bed_name.ilike(pattern), Bed.bed_code.ilike(pattern))).limit(limit))]
        accommodation = accommodation[:limit]
    cases = [SearchResult(module="case_management", id=r.id, display_title=r.case_number, display_subtitle=f"Risk: {r.risk_level}", status=r.case_status) for r in db.scalars(select(ChildCaseProfile).where(ChildCaseProfile.deleted_at.is_(None), ChildCaseProfile.case_number.ilike(pattern)).limit(limit))] if include("case_management") else empty
    return GlobalSearchResponse(query=q, children=children, sponsors=sponsors, education=education, accommodation=accommodation, case_management=cases)
