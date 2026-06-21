from datetime import date, timedelta
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
from app.models.child import Child
from app.models.medical_document import MedicalDocument
from app.models.medical_profile import MedicalProfile
from app.models.medical_visit import MedicalVisit
from app.models.medication import Medication
from app.models.user import User
from app.models.vaccination import Vaccination
from app.schemas.medical import (
    MedicalDashboard,
    MedicalDocumentResponse,
    MedicalDocumentType,
    MedicalProfileCreate,
    MedicalProfileResponse,
    MedicalProfileUpdate,
    MedicalVisitCreate,
    MedicalVisitResponse,
    MedicalVisitUpdate,
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
    VaccinationCreate,
    VaccinationResponse,
    VaccinationUpdate,
)
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.utils.files import enforce_upload_size, safe_upload_directory, sanitize_filename

router = APIRouter(tags=["Medical"])
ALLOWED_MEDICAL_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


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


def audit_medical(
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
        module=AuditModule.MEDICAL,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
    )


def update_medical_record(
    db: Session,
    record,
    changes: dict,
    user: User,
    action: AuditAction,
):
    if not changes:
        return record
    old_values = {key: getattr(record, key) for key in changes}
    for key, value in changes.items():
        setattr(record, key, value)
    record.updated_by = user.id
    audit_medical(
        db,
        user,
        action,
        record.id,
        old_values=old_values,
        new_values=changes,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail="Invalid medical record data") from exc
    db.refresh(record)
    return record


@router.post(
    "/children/{child_id}/medical-profile",
    response_model=MedicalProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a child's medical profile",
)
def create_medical_profile(
    child_id: int,
    payload: MedicalProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(can_create_or_update),
):
    child_or_404(db, child_id)
    if db.scalar(select(MedicalProfile.id).where(MedicalProfile.child_id == child_id)):
        raise HTTPException(status_code=409, detail="Medical profile already exists for child")
    profile = MedicalProfile(
        child_id=child_id,
        **payload.model_dump(mode="json"),
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(profile)
    try:
        db.flush()
        audit_medical(
            db,
            user,
            AuditAction.MEDICAL_PROFILE_CREATE,
            profile.id,
            new_values=snapshot(profile),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Medical profile already exists for child") from exc
    db.refresh(profile)
    return profile


@router.get("/children/{child_id}/medical-profile", response_model=MedicalProfileResponse)
def get_medical_profile(
    child_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(can_operational_read),
):
    child_or_404(db, child_id)
    profile = db.scalar(select(MedicalProfile).where(MedicalProfile.child_id == child_id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Medical profile not found")
    return profile


@router.put("/children/{child_id}/medical-profile", response_model=MedicalProfileResponse)
def update_medical_profile(
    child_id: int,
    payload: MedicalProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(can_create_or_update),
):
    profile = db.scalar(select(MedicalProfile).where(MedicalProfile.child_id == child_id))
    if profile is None:
        child_or_404(db, child_id)
        raise HTTPException(status_code=404, detail="Medical profile not found")
    return update_medical_record(
        db,
        profile,
        payload.model_dump(exclude_unset=True, mode="json"),
        user,
        AuditAction.MEDICAL_PROFILE_UPDATE,
    )


@router.post("/children/{child_id}/medical-visits", response_model=MedicalVisitResponse, status_code=201)
def create_medical_visit(child_id: int, payload: MedicalVisitCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id)
    record = MedicalVisit(child_id=child_id, **payload.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(record); db.flush(); audit_medical(db, user, AuditAction.MEDICAL_VISIT_CREATE, record.id, new_values=snapshot(record)); db.commit(); db.refresh(record)
    return record


@router.get("/children/{child_id}/medical-visits", response_model=list[MedicalVisitResponse])
def list_child_medical_visits(child_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    return db.scalars(select(MedicalVisit).where(MedicalVisit.child_id == child_id).order_by(MedicalVisit.visit_date.desc(), MedicalVisit.id.desc()).offset(skip).limit(limit)).all()


@router.get("/medical-visits/{visit_id}", response_model=MedicalVisitResponse)
def get_medical_visit(visit_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return record_or_404(db, MedicalVisit, visit_id, "Medical visit")


@router.put("/medical-visits/{visit_id}", response_model=MedicalVisitResponse)
def update_medical_visit(visit_id: int, payload: MedicalVisitUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    return update_medical_record(db, record_or_404(db, MedicalVisit, visit_id, "Medical visit"), payload.model_dump(exclude_unset=True), user, AuditAction.MEDICAL_VISIT_UPDATE)


@router.post("/children/{child_id}/medications", response_model=MedicationResponse, status_code=201)
def create_medication(child_id: int, payload: MedicationCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id)
    record = Medication(child_id=child_id, **payload.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(record); db.flush(); audit_medical(db, user, AuditAction.MEDICATION_CREATE, record.id, new_values=snapshot(record)); db.commit(); db.refresh(record)
    return record


@router.get("/children/{child_id}/medications", response_model=list[MedicationResponse])
def list_child_medications(child_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    return db.scalars(select(Medication).where(Medication.child_id == child_id).order_by(Medication.start_date.desc(), Medication.id.desc()).offset(skip).limit(limit)).all()


@router.put("/medications/{medication_id}", response_model=MedicationResponse)
def update_medication(medication_id: int, payload: MedicationUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = record_or_404(db, Medication, medication_id, "Medication")
    changes = payload.model_dump(exclude_unset=True)
    effective_start = changes.get("start_date", record.start_date)
    effective_end = changes.get("end_date", record.end_date)
    if effective_end is not None and effective_end < effective_start:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    return update_medical_record(db, record, changes, user, AuditAction.MEDICATION_UPDATE)


@router.post("/children/{child_id}/vaccinations", response_model=VaccinationResponse, status_code=201)
def create_vaccination(child_id: int, payload: VaccinationCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id)
    record = Vaccination(child_id=child_id, **payload.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(record); db.flush(); audit_medical(db, user, AuditAction.VACCINATION_CREATE, record.id, new_values=snapshot(record)); db.commit(); db.refresh(record)
    return record


@router.get("/children/{child_id}/vaccinations", response_model=list[VaccinationResponse])
def list_child_vaccinations(child_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    return db.scalars(select(Vaccination).where(Vaccination.child_id == child_id).order_by(Vaccination.vaccination_date.desc(), Vaccination.id.desc()).offset(skip).limit(limit)).all()


@router.put("/vaccinations/{vaccination_id}", response_model=VaccinationResponse)
def update_vaccination(vaccination_id: int, payload: VaccinationUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = record_or_404(db, Vaccination, vaccination_id, "Vaccination")
    changes = payload.model_dump(exclude_unset=True)
    effective_date = changes.get("vaccination_date", record.vaccination_date)
    effective_due = changes.get("next_due_date", record.next_due_date)
    if effective_due is not None and effective_due < effective_date:
        raise HTTPException(status_code=422, detail="next_due_date must be on or after vaccination_date")
    return update_medical_record(db, record, changes, user, AuditAction.VACCINATION_UPDATE)


@router.post("/medical-documents/upload", response_model=MedicalDocumentResponse, status_code=201)
def upload_medical_document(
    child_id: int = Form(...),
    document_type: MedicalDocumentType = Form(...),
    medical_visit_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(can_create_or_update),
):
    child = child_or_404(db, child_id)
    if medical_visit_id is not None:
        visit = record_or_404(db, MedicalVisit, medical_visit_id, "Medical visit")
        if visit.child_id != child_id:
            raise HTTPException(status_code=422, detail="Medical visit does not belong to child")
    original_name = sanitize_filename(file.filename)
    enforce_upload_size(file)
    extension = Path(original_name).suffix.lower()
    if not original_name or len(original_name) > 200:
        raise HTTPException(status_code=422, detail="Invalid filename")
    if extension not in ALLOWED_MEDICAL_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Medical documents accept PDF, JPG, JPEG, or PNG")

    folder = safe_upload_directory(child.child_id, "medical")
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = folder / stored_name
    try:
        with file_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        document = MedicalDocument(
            child_id=child_id,
            medical_visit_id=medical_visit_id,
            document_type=document_type.value,
            original_filename=original_name,
            stored_filename=stored_name,
            file_path=str(file_path),
            uploaded_by=user.id,
        )
        db.add(document)
        db.flush()
        audit_medical(db, user, AuditAction.MEDICAL_DOCUMENT_UPLOAD, document.id, new_values=snapshot(document))
        db.commit()
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise
    db.refresh(document)
    return document


@router.get("/children/{child_id}/medical-documents", response_model=list[MedicalDocumentResponse])
def list_medical_documents(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    return db.scalars(select(MedicalDocument).where(MedicalDocument.child_id == child_id).order_by(MedicalDocument.uploaded_at.desc(), MedicalDocument.id.desc())).all()


@router.delete("/medical-documents/{document_id}")
def delete_medical_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    document = record_or_404(db, MedicalDocument, document_id, "Medical document")
    old_values = snapshot(document)
    file_path = Path(document.file_path)
    db.delete(document)
    audit_medical(db, user, AuditAction.MEDICAL_DOCUMENT_DELETE, document_id, old_values=old_values)
    db.commit()
    file_path.unlink(missing_ok=True)
    return {"message": "Medical document deleted successfully", "document_id": document_id}


@router.get("/reports/medical-profiles", response_model=list[MedicalProfileResponse], tags=["Medical Reports"])
def report_medical_profiles(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(MedicalProfile).order_by(MedicalProfile.child_id).offset(skip).limit(limit)).all()


@router.get("/reports/medical-visits", response_model=list[MedicalVisitResponse], tags=["Medical Reports"])
def report_medical_visits(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(MedicalVisit).order_by(MedicalVisit.visit_date.desc()).offset(skip).limit(limit)).all()


@router.get("/reports/chronic-diseases", response_model=list[MedicalProfileResponse], tags=["Medical Reports"])
def report_chronic_diseases(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(MedicalProfile).where(MedicalProfile.chronic_diseases.is_not(None), func.trim(MedicalProfile.chronic_diseases) != "").order_by(MedicalProfile.child_id)).all()


@router.get("/reports/special-needs", response_model=list[MedicalProfileResponse], tags=["Medical Reports"])
def report_special_needs(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(MedicalProfile).where(MedicalProfile.special_needs.is_not(None), func.trim(MedicalProfile.special_needs) != "").order_by(MedicalProfile.child_id)).all()


@router.get("/reports/active-medications", response_model=list[MedicationResponse], tags=["Medical Reports"])
def report_active_medications(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(Medication).where(Medication.status == "Active").order_by(Medication.start_date.desc())).all()


@router.get("/reports/upcoming-vaccinations", response_model=list[VaccinationResponse], tags=["Medical Reports"])
def report_upcoming_vaccinations(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    today = date.today()
    return db.scalars(select(Vaccination).where(Vaccination.next_due_date.between(today, today + timedelta(days=30))).order_by(Vaccination.next_due_date)).all()


@router.get("/dashboard/medical", response_model=MedicalDashboard, tags=["Medical Dashboard"])
def medical_dashboard(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    today = date.today()
    month_start = today.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    scalar_count = lambda statement: db.scalar(statement) or 0
    return MedicalDashboard(
        total_children=scalar_count(select(func.count()).select_from(Child)),
        children_with_medical_profiles=scalar_count(select(func.count()).select_from(MedicalProfile)),
        active_medications=scalar_count(select(func.count()).select_from(Medication).where(Medication.status == "Active")),
        upcoming_vaccinations=scalar_count(select(func.count()).select_from(Vaccination).where(Vaccination.next_due_date.between(today, today + timedelta(days=30)))),
        children_with_special_needs=scalar_count(select(func.count()).select_from(MedicalProfile).where(MedicalProfile.special_needs.is_not(None), func.trim(MedicalProfile.special_needs) != "")),
        medical_visits_this_month=scalar_count(select(func.count()).select_from(MedicalVisit).where(MedicalVisit.visit_date >= month_start, MedicalVisit.visit_date < next_month)),
    )
