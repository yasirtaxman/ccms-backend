from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.core.deps import can_create_or_update, can_operational_read, get_db, require_admin
from app.models.attendance import Attendance
from app.models.child import Child
from app.models.education_document import EducationDocument
from app.models.education_record import EducationRecord
from app.models.exam_result import ExamResult
from app.models.school import School
from app.models.user import User
from app.schemas.education import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    EducationDashboard,
    EducationDocumentResponse,
    EducationDocumentType,
    EducationRecordCreate,
    EducationRecordResponse,
    EducationRecordUpdate,
    ExamResultCreate,
    ExamResultResponse,
    ExamResultUpdate,
    SchoolCreate,
    SchoolResponse,
    SchoolUpdate,
)
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter(tags=["Education"])
ALLOWED_EDUCATION_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def snapshot(instance) -> dict:
    return jsonable_encoder(
        {column.key: getattr(instance, column.key) for column in inspect(instance).mapper.column_attrs}
    )


def child_or_404(db: Session, child_id: int) -> Child:
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


def record_or_404(db: Session, model, record_id: int, label: str):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return record


def audit_education(
    db: Session,
    user: User,
    action: AuditAction,
    record_id: int,
    *,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    add_audit_log(
        db,
        user_id=user.id,
        action=action,
        module=AuditModule.EDUCATION,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
    )


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def calculated_percentage(value: Decimal, total: Decimal) -> Decimal:
    return ((value * Decimal("100")) / total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def update_record(db: Session, record, changes: dict, user: User, action: AuditAction):
    if not changes:
        return record
    old_values = {key: getattr(record, key) for key in changes}
    for key, value in changes.items():
        setattr(record, key, value)
    record.updated_by = user.id
    audit_education(db, user, action, record.id, old_values=old_values, new_values=changes)
    commit_or_conflict(db, "Duplicate or invalid education data")
    db.refresh(record)
    return record


@router.post("/schools", response_model=SchoolResponse, status_code=201)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    values = payload.model_dump(mode="json")
    values["school_code"] = values["school_code"].strip().upper()
    school = School(**values, created_by=user.id, updated_by=user.id)
    db.add(school)
    try:
        db.flush()
        audit_education(db, user, AuditAction.SCHOOL_CREATE, school.id, new_values=snapshot(school))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="School code already exists") from exc
    db.refresh(school)
    return school


@router.get("/schools", response_model=list[SchoolResponse])
def list_schools(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(School).order_by(School.school_code).offset(skip).limit(limit)).all()


@router.get("/schools/{school_id}", response_model=SchoolResponse)
def get_school(school_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return record_or_404(db, School, school_id, "School")


@router.put("/schools/{school_id}", response_model=SchoolResponse)
def update_school(school_id: int, payload: SchoolUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if changes.get("school_code"):
        changes["school_code"] = changes["school_code"].strip().upper()
    return update_record(db, record_or_404(db, School, school_id, "School"), changes, user, AuditAction.SCHOOL_UPDATE)


@router.delete("/schools/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    school = record_or_404(db, School, school_id, "School")
    if db.scalar(select(EducationRecord.id).where(EducationRecord.school_id == school.id).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete a school with education history")
    old_values = snapshot(school)
    db.delete(school)
    audit_education(db, user, AuditAction.SCHOOL_DELETE, school_id, old_values=old_values)
    db.commit()
    return {"message": "School deleted successfully", "school_id": school_id}


def ensure_single_active_record(db: Session, child_id: int, *, exclude_id: int | None = None) -> None:
    statement = select(EducationRecord.id).where(
        EducationRecord.child_id == child_id,
        EducationRecord.status == "Studying",
    )
    if exclude_id is not None:
        statement = statement.where(EducationRecord.id != exclude_id)
    if db.scalar(statement.limit(1)):
        raise HTTPException(status_code=409, detail="Child already has an active education record")


@router.post("/children/{child_id}/education-records", response_model=EducationRecordResponse, status_code=201)
def create_education_record(child_id: int, payload: EducationRecordCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id)
    school = record_or_404(db, School, payload.school_id, "School")
    if payload.status.value == "Studying":
        if school.status != "Active":
            raise HTTPException(status_code=409, detail="Cannot enroll a child in an inactive school")
        ensure_single_active_record(db, child_id)
    record = EducationRecord(child_id=child_id, **payload.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush()
        audit_education(db, user, AuditAction.EDUCATION_RECORD_CREATE, record.id, new_values=snapshot(record))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Child already has an active education record") from exc
    db.refresh(record)
    return record


@router.get("/children/{child_id}/education-records", response_model=list[EducationRecordResponse])
def list_child_education_records(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    return db.scalars(select(EducationRecord).where(EducationRecord.child_id == child_id).order_by(EducationRecord.start_date.desc(), EducationRecord.id.desc())).all()


@router.get("/education-records/{record_id}", response_model=EducationRecordResponse)
def get_education_record(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return record_or_404(db, EducationRecord, record_id, "Education record")


@router.put("/education-records/{record_id}", response_model=EducationRecordResponse)
def update_education_record(record_id: int, payload: EducationRecordUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = record_or_404(db, EducationRecord, record_id, "Education record")
    changes = payload.model_dump(exclude_unset=True)
    effective_start = changes.get("start_date", record.start_date)
    effective_end = changes.get("end_date", record.end_date)
    if effective_end is not None and effective_end < effective_start:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    if changes.get("status") == "Studying" and record.status != "Studying":
        school = record_or_404(db, School, record.school_id, "School")
        if school.status != "Active":
            raise HTTPException(status_code=409, detail="Cannot activate enrollment at an inactive school")
        ensure_single_active_record(db, record.child_id, exclude_id=record.id)
    return update_record(db, record, changes, user, AuditAction.EDUCATION_RECORD_UPDATE)


@router.post("/education-records/{record_id}/results", response_model=ExamResultResponse, status_code=201)
def create_exam_result(record_id: int, payload: ExamResultCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record_or_404(db, EducationRecord, record_id, "Education record")
    result = ExamResult(education_record_id=record_id, **payload.model_dump(), percentage=calculated_percentage(payload.obtained_marks, payload.total_marks), created_by=user.id, updated_by=user.id)
    db.add(result); db.flush(); audit_education(db, user, AuditAction.EXAM_RESULT_CREATE, result.id, new_values=snapshot(result)); db.commit(); db.refresh(result)
    return result


@router.get("/education-records/{record_id}/results", response_model=list[ExamResultResponse])
def list_exam_results(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    record_or_404(db, EducationRecord, record_id, "Education record")
    return db.scalars(select(ExamResult).where(ExamResult.education_record_id == record_id).order_by(ExamResult.exam_date.desc(), ExamResult.id.desc())).all()


@router.put("/results/{result_id}", response_model=ExamResultResponse)
def update_exam_result(result_id: int, payload: ExamResultUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    result = record_or_404(db, ExamResult, result_id, "Exam result")
    changes = payload.model_dump(exclude_unset=True)
    total = changes.get("total_marks", result.total_marks)
    obtained = changes.get("obtained_marks", result.obtained_marks)
    if obtained > total:
        raise HTTPException(status_code=422, detail="obtained_marks cannot exceed total_marks")
    if "total_marks" in changes or "obtained_marks" in changes:
        changes["percentage"] = calculated_percentage(obtained, total)
    return update_record(db, result, changes, user, AuditAction.EXAM_RESULT_UPDATE)


@router.post("/education-records/{record_id}/attendance", response_model=AttendanceResponse, status_code=201)
def create_attendance(record_id: int, payload: AttendanceCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record_or_404(db, EducationRecord, record_id, "Education record")
    attendance = Attendance(education_record_id=record_id, **payload.model_dump(), attendance_percentage=calculated_percentage(Decimal(payload.present_days), Decimal(payload.total_days)), created_by=user.id, updated_by=user.id)
    db.add(attendance)
    try:
        db.flush(); audit_education(db, user, AuditAction.ATTENDANCE_CREATE, attendance.id, new_values=snapshot(attendance)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Attendance already exists for this month and year") from exc
    db.refresh(attendance); return attendance


@router.get("/education-records/{record_id}/attendance", response_model=list[AttendanceResponse])
def list_attendance(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    record_or_404(db, EducationRecord, record_id, "Education record")
    return db.scalars(select(Attendance).where(Attendance.education_record_id == record_id).order_by(Attendance.year.desc(), Attendance.month.desc())).all()


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(attendance_id: int, payload: AttendanceUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    attendance = record_or_404(db, Attendance, attendance_id, "Attendance")
    changes = payload.model_dump(exclude_unset=True)
    total = changes.get("total_days", attendance.total_days)
    present = changes.get("present_days", attendance.present_days)
    absent = changes.get("absent_days", attendance.absent_days)
    if present + absent != total:
        raise HTTPException(status_code=422, detail="present_days plus absent_days must equal total_days")
    if {"total_days", "present_days", "absent_days"} & changes.keys():
        changes["attendance_percentage"] = calculated_percentage(Decimal(present), Decimal(total))
    return update_record(db, attendance, changes, user, AuditAction.ATTENDANCE_UPDATE)


@router.post("/education-documents/upload", response_model=EducationDocumentResponse, status_code=201)
def upload_education_document(
    child_id: int = Form(...),
    document_type: EducationDocumentType = Form(...),
    education_record_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(can_create_or_update),
):
    child = child_or_404(db, child_id)
    if education_record_id is not None:
        education_record = record_or_404(db, EducationRecord, education_record_id, "Education record")
        if education_record.child_id != child_id:
            raise HTTPException(status_code=422, detail="Education record does not belong to child")
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()
    if not original_name or len(original_name) > 200:
        raise HTTPException(status_code=422, detail="Invalid filename")
    if extension not in ALLOWED_EDUCATION_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Education documents accept PDF, JPG, JPEG, or PNG")
    folder = Path("uploads") / child.child_id / "education"
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = folder / stored_name
    try:
        with file_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        document = EducationDocument(child_id=child_id, education_record_id=education_record_id, document_type=document_type.value, original_filename=original_name, stored_filename=stored_name, file_path=str(file_path), uploaded_by=user.id)
        db.add(document); db.flush(); audit_education(db, user, AuditAction.EDUCATION_DOCUMENT_UPLOAD, document.id, new_values=snapshot(document)); db.commit()
    except Exception:
        db.rollback(); file_path.unlink(missing_ok=True); raise
    db.refresh(document); return document


@router.get("/children/{child_id}/education-documents", response_model=list[EducationDocumentResponse])
def list_education_documents(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    return db.scalars(select(EducationDocument).where(EducationDocument.child_id == child_id).order_by(EducationDocument.uploaded_at.desc())).all()


@router.delete("/education-documents/{document_id}")
def delete_education_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    document = record_or_404(db, EducationDocument, document_id, "Education document")
    old_values = snapshot(document); file_path = Path(document.file_path); db.delete(document)
    audit_education(db, user, AuditAction.EDUCATION_DOCUMENT_DELETE, document_id, old_values=old_values)
    db.commit(); file_path.unlink(missing_ok=True)
    return {"message": "Education document deleted successfully", "document_id": document_id}


@router.get("/reports/students", response_model=list[EducationRecordResponse], tags=["Education Reports"])
def report_students(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(EducationRecord).order_by(EducationRecord.start_date.desc())).all()


@router.get("/reports/schools", response_model=list[SchoolResponse], tags=["Education Reports"])
def report_schools(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(School).order_by(School.school_name)).all()


@router.get("/reports/exam-results", response_model=list[ExamResultResponse], tags=["Education Reports"])
def report_exam_results(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(ExamResult).order_by(ExamResult.exam_date.desc())).all()


@router.get("/reports/top-performers", response_model=list[ExamResultResponse], tags=["Education Reports"])
def report_top_performers(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(ExamResult).order_by(ExamResult.percentage.desc(), ExamResult.exam_date.desc()).limit(limit)).all()


@router.get("/reports/low-attendance", response_model=list[AttendanceResponse], tags=["Education Reports"])
def report_low_attendance(threshold: Decimal = Query(Decimal("75"), ge=0, le=100), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(Attendance).where(Attendance.attendance_percentage < threshold).order_by(Attendance.attendance_percentage)).all()


@router.get("/reports/dropout-students", response_model=list[EducationRecordResponse], tags=["Education Reports"])
def report_dropout_students(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(EducationRecord).where(EducationRecord.status == "Dropped").order_by(EducationRecord.end_date.desc())).all()


@router.get("/reports/board-exam-students", response_model=list[EducationRecordResponse], tags=["Education Reports"])
def report_board_exam_students(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    record_ids = select(ExamResult.education_record_id).where(ExamResult.exam_name == "Board").distinct()
    return db.scalars(select(EducationRecord).where(EducationRecord.id.in_(record_ids)).order_by(EducationRecord.child_id)).all()


@router.get("/dashboard/education", response_model=EducationDashboard, tags=["Education Dashboard"])
def education_dashboard(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    scalar = lambda statement: db.scalar(statement) or 0
    return EducationDashboard(
        total_students=scalar(select(func.count(func.distinct(EducationRecord.child_id)))),
        active_students=scalar(select(func.count()).select_from(EducationRecord).where(EducationRecord.status == "Studying")),
        schools_count=scalar(select(func.count()).select_from(School).where(School.status == "Active")),
        average_attendance=round(float(scalar(select(func.avg(Attendance.attendance_percentage)))), 2),
        average_marks=round(float(scalar(select(func.avg(ExamResult.percentage)))), 2),
        board_students=scalar(select(func.count(func.distinct(EducationRecord.child_id))).select_from(EducationRecord).join(ExamResult, ExamResult.education_record_id == EducationRecord.id).where(ExamResult.exam_name == "Board")),
        dropout_students=scalar(select(func.count(func.distinct(EducationRecord.child_id))).where(EducationRecord.status == "Dropped")),
    )
