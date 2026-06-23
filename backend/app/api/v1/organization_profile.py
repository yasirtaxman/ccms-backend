from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import ROLE_DATA_ENTRY, ROLE_MANAGER, ROLE_VIEWER, get_db, require_admin, require_roles
from app.models.user import User
from app.schemas.organization_profile import OrganizationProfileResponse, OrganizationProfileUpdate
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.organization_profile_service import delete_logo, logo_file_path, public_profile, save_logo, upsert_profile

router = APIRouter(prefix="/organization-profile", tags=["Organization Profile"])
can_read_branding = require_roles(ROLE_MANAGER, ROLE_DATA_ENTRY, ROLE_VIEWER, "Warden")


@router.get("", response_model=OrganizationProfileResponse)
def get_organization_profile(
    db: Session = Depends(get_db),
    _user: User = Depends(can_read_branding),
):
    return public_profile(db)


@router.put("", response_model=OrganizationProfileResponse)
def update_organization_profile(
    payload: OrganizationProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    profile = upsert_profile(db, payload)
    add_audit_log(
        db,
        user_id=user.id,
        action=AuditAction.ORGANIZATION_PROFILE_UPDATED,
        module=AuditModule.ORGANIZATION_PROFILE,
        record_id=profile.id,
        new_values=payload.model_dump(),
    )
    db.commit()
    return public_profile(db)


@router.post("/logo", response_model=OrganizationProfileResponse)
def upload_organization_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    profile = save_logo(db, file)
    add_audit_log(
        db,
        user_id=user.id,
        action=AuditAction.ORGANIZATION_LOGO_UPLOADED,
        module=AuditModule.ORGANIZATION_PROFILE,
        record_id=profile.id,
        new_values={"filename": file.filename},
    )
    db.commit()
    return public_profile(db)


@router.get("/logo")
def get_organization_logo(
    db: Session = Depends(get_db),
    _user: User = Depends(can_read_branding),
):
    path = logo_file_path(db)
    if path is None:
        raise HTTPException(status_code=404, detail="Organization logo is not configured")
    return FileResponse(path)


@router.delete("/logo", response_model=OrganizationProfileResponse)
def delete_organization_logo(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    profile = delete_logo(db)
    add_audit_log(
        db,
        user_id=user.id,
        action=AuditAction.ORGANIZATION_LOGO_DELETED,
        module=AuditModule.ORGANIZATION_PROFILE,
        record_id=profile.id,
    )
    db.commit()
    return public_profile(db)
