from pathlib import Path
import shutil
import uuid
import os

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import can_create_or_update, can_read, get_db, require_admin
from app.models.document import Document
from app.models.child import Child
from app.models.user import User
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter()


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

    allowed_extensions = {
        "Admission Form": [".pdf"],
        "Affidavit": [".pdf"],
        "Death Certificate": [".pdf", ".jpg", ".jpeg", ".png"],
        "Father CNIC": [".pdf", ".jpg", ".jpeg", ".png"],
        "Guardian CNIC": [".pdf", ".jpg", ".jpeg", ".png"],
        "Birth Certificate": [".pdf", ".jpg", ".jpeg", ".png"],
        "Child Photo": [".jpg", ".jpeg", ".png"]
    }

    file_extension = Path(file.filename).suffix.lower()

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

    folder_mapping = {
        "Admission Form": "admission_forms",
        "Affidavit": "affidavits",
        "Death Certificate": "death_certificates",
        "Father CNIC": "father_cnic",
        "Guardian CNIC": "guardian_cnic",
        "Birth Certificate": "birth_certificates",
        "Child Photo": "child_photos"
    }

    document_folder = folder_mapping.get(
        document_type,
        "misc"
    )

    child_folder = (
        Path("uploads")
        / child.child_id
        / document_folder
    )

    child_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
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
        original_filename=file.filename,
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
            "original_filename": file.filename,
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
    _current_user: User = Depends(can_read),
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
    _current_user: User = Depends(can_read),
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

    document_types = {
        doc.document_type for doc in documents
    }

    admission_form = "Admission Form" in document_types
    affidavit = "Affidavit" in document_types
    death_certificate = "Death Certificate" in document_types
    father_cnic = "Father CNIC" in document_types
    guardian_cnic = "Guardian CNIC" in document_types
    birth_certificate = "Birth Certificate" in document_types
    child_photo = "Child Photo" in document_types

    admission_complete = all([
        admission_form,
        affidavit,
        death_certificate,
        father_cnic,
        guardian_cnic,
        birth_certificate,
        child_photo
    ])

    return {
        "child_id": child.child_id,
        "admission_form": admission_form,
        "affidavit": affidavit,
        "death_certificate": death_certificate,
        "father_cnic": father_cnic,
        "guardian_cnic": guardian_cnic,
        "birth_certificate": birth_certificate,
        "child_photo": child_photo,
        "admission_complete": admission_complete
    }
