from pathlib import Path
import shutil
import uuid
import os

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import can_create_or_update, can_operational_read, get_db, require_admin
from app.models.document import Document
from app.models.child import Child
from app.models.user import User
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.utils.files import enforce_upload_size, safe_upload_directory, sanitize_filename

router = APIRouter()

ADMISSION_DOCUMENT_TYPES = [
    {"document_type": "Admission Form", "required": True, "extensions": ["pdf"]},
    {"document_type": "Child Photo", "required": True, "extensions": ["jpg", "jpeg", "png"]},
    {"document_type": "Birth Certificate / Form-B", "required": True, "extensions": ["pdf", "jpg", "jpeg", "png"]},
    {"document_type": "Guardian CNIC", "required": True, "extensions": ["pdf", "jpg", "jpeg", "png"]},
    {"document_type": "Father Death Certificate", "required": True, "extensions": ["pdf", "jpg", "jpeg", "png"]},
    {"document_type": "Medical Certificate", "required": True, "extensions": ["pdf", "jpg", "jpeg", "png"]},
    {"document_type": "School / Education Record", "required": False, "extensions": ["pdf", "jpg", "jpeg", "png"]},
    {"document_type": "Court / Legal Order", "required": False, "extensions": ["pdf", "jpg", "jpeg", "png"]},
    {"document_type": "Other Supporting Document", "required": False, "extensions": ["pdf", "jpg", "jpeg", "png"]},
]


@router.post("/documents/upload")
def upload_document(
    child_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    child = db.query(Child).filter(
        Child.id == child_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found"
        )

    allowed_extensions = {item["document_type"]: [f'.{ext}' for ext in item["extensions"]] for item in ADMISSION_DOCUMENT_TYPES}
    allowed_extensions.update({"Affidavit":[".pdf"],"Death Certificate":[".pdf",".jpg",".jpeg",".png"],"Father CNIC":[".pdf",".jpg",".jpeg",".png"],"Birth Certificate":[".pdf",".jpg",".jpeg",".png"]})

    original_name = sanitize_filename(file.filename)
    enforce_upload_size(file)
    file_extension = Path(original_name).suffix.lower()

    if document_type not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {document_type}"
        )

    if file_extension not in allowed_extensions[document_type]:
        raise HTTPException(
            status_code=400,
            detail=f"{document_type} only accepts: {', '.join(allowed_extensions[document_type])}"
        )

    document_folder = document_type.lower().replace(" / ", "_").replace(" ", "_").replace("-", "_")

    child_folder = safe_upload_directory(child.child_id, document_folder)

    unique_filename = (
        f"{uuid.uuid4()}_{original_name}"
    )

    file_path = child_folder / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    document = Document(
        child_id=child_id,
        document_type=document_type,
        original_filename=original_name,
        stored_filename=unique_filename,
        file_path=str(file_path),
        is_verified=False
    )

    db.add(document)
    db.flush()
    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        module=AuditModule.DOCUMENTS,
        record_id=document.id,
        new_values={
            "child_id": child_id,
            "document_type": document_type,
            "original_filename": original_name,
            "is_verified": False,
        },
    )
    db.commit()
    db.refresh(document)

    return document


@router.get("/children/{child_id}/documents")
def get_child_documents(
    child_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_operational_read),
):
    child = db.query(Child).filter(
        Child.id == child_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found"
        )

    documents = db.query(Document).filter(
        Document.child_id == child_id
    ).all()

    return documents


@router.post("/documents/{document_id}/verify")
def verify_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    document.is_verified = True

    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.VERIFY,
        module=AuditModule.DOCUMENTS,
        record_id=document.id,
        old_values={"is_verified": False},
        new_values={"is_verified": True},
    )

    db.commit()
    db.refresh(document)

    return {
        "message": "Document verified successfully",
        "document_id": document.id,
        "verified": document.is_verified
    }


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    file_path = document.file_path
    old_values = {
        "child_id": document.child_id,
        "document_type": document.document_type,
        "original_filename": document.original_filename,
        "is_verified": document.is_verified,
    }

    db.delete(document)
    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        module=AuditModule.DOCUMENTS,
        record_id=document_id,
        old_values=old_values,
    )
    db.commit()

    if os.path.exists(file_path):
        os.remove(file_path)

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }


@router.get("/children/{child_id}/admission-checklist")
def admission_checklist(
    child_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_operational_read),
):
    child = db.query(Child).filter(
        Child.id == child_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found"
        )

    documents = db.query(Document).filter(
        Document.child_id == child_id
    ).all()

    checklist = _build_checklist(documents);document_types={doc.document_type for doc in documents}
    return {"child_id": child.child_id, "admission_form":"Admission Form" in document_types,"affidavit":"Affidavit" in document_types,"death_certificate":"Death Certificate" in document_types,"father_cnic":"Father CNIC" in document_types,"guardian_cnic":"Guardian CNIC" in document_types,"birth_certificate":"Birth Certificate" in document_types,"child_photo":"Child Photo" in document_types,"items": checklist, "admission_complete": all(item["uploaded"] and item["verified"] for item in checklist if item["required"])}


@router.get("/documents/admission-document-types", tags=["Documents"])
def admission_document_types(_current_user: User = Depends(can_operational_read)):
    return ADMISSION_DOCUMENT_TYPES


@router.get("/children/{child_id}/documents/checklist", tags=["Documents"])
def document_checklist(child_id: int, db: Session = Depends(get_db), _current_user: User = Depends(can_operational_read)):
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return _build_checklist(db.query(Document).filter(Document.child_id == child_id).all())


def _build_checklist(documents):
    result = []
    for definition in ADMISSION_DOCUMENT_TYPES:
        matches = [doc for doc in documents if doc.document_type == definition["document_type"]]
        latest = max(matches, key=lambda doc: doc.id) if matches else None
        verified = any(doc.is_verified for doc in matches)
        uploaded = bool(matches)
        result.append({
            "document_type": definition["document_type"], "required": definition["required"],
            "uploaded": uploaded, "verified": verified, "uploaded_count": len(matches),
            "latest_document_id": latest.id if latest else None,
            "status": "Verified" if verified else "Pending verification" if uploaded else "Missing",
        })
    return result
