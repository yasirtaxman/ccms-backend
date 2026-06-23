from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization_profile import OrganizationProfile
from app.schemas.organization_profile import OrganizationProfileResponse, OrganizationProfileUpdate
from app.utils.files import enforce_upload_size, safe_upload_directory, sanitize_filename


ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def default_branding() -> dict:
    return {
        "id": None,
        "organization_name": "Child Care Management System",
        "short_name": "CCMS",
        "logo_path": None,
        "logo_url": None,
        "address": "Not configured",
        "city": None,
        "district": None,
        "province": None,
        "country": None,
        "phone": None,
        "email": None,
        "website": None,
        "registration_no": None,
        "ntn_or_tax_no": None,
        "report_footer_text": "This report is system generated.",
        "report_watermark_text": None,
        "primary_color": "#174A7E",
        "secondary_color": "#EAF2F9",
        "authorized_signatory_name": None,
        "authorized_signatory_designation": None,
        "is_active": True,
    }


def get_active_profile(db: Session) -> OrganizationProfile | None:
    return db.scalar(select(OrganizationProfile).where(OrganizationProfile.is_active.is_(True)).order_by(OrganizationProfile.id.desc()))


def logo_url(profile: OrganizationProfile | None) -> str | None:
    if not profile or not profile.logo_path:
        return None
    return "/organization-profile/logo"


def public_profile(db: Session) -> OrganizationProfileResponse:
    profile = get_active_profile(db)
    if profile is None:
        return OrganizationProfileResponse(**default_branding())
    return OrganizationProfileResponse(
        id=profile.id,
        organization_name=profile.organization_name,
        short_name=profile.short_name,
        address=profile.address,
        city=profile.city,
        district=profile.district,
        province=profile.province,
        country=profile.country,
        phone=profile.phone,
        email=profile.email,
        website=profile.website,
        registration_no=profile.registration_no,
        ntn_or_tax_no=profile.ntn_or_tax_no,
        report_footer_text=profile.report_footer_text,
        report_watermark_text=profile.report_watermark_text,
        primary_color=profile.primary_color,
        secondary_color=profile.secondary_color,
        authorized_signatory_name=profile.authorized_signatory_name,
        authorized_signatory_designation=profile.authorized_signatory_designation,
        is_active=profile.is_active,
        logo_url=logo_url(profile),
    )


def report_branding(db: Session) -> dict:
    profile = get_active_profile(db)
    branding = default_branding()
    if profile is None:
        return branding
    for key in branding:
        if hasattr(profile, key):
            value = getattr(profile, key)
            if value not in (None, ""):
                branding[key] = value
    branding["logo_url"] = logo_url(profile)
    return branding


def upsert_profile(db: Session, payload: OrganizationProfileUpdate) -> OrganizationProfile:
    profile = get_active_profile(db)
    if profile is None:
        profile = OrganizationProfile(**payload.model_dump())
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    db.flush()
    return profile


def logo_file_path(db: Session) -> Path | None:
    profile = get_active_profile(db)
    if not profile or not profile.logo_path:
        return None
    path = Path(profile.logo_path)
    if not path.is_file():
        return None
    return path


def save_logo(db: Session, file: UploadFile) -> OrganizationProfile:
    profile = get_active_profile(db)
    if profile is None:
        profile = OrganizationProfile(
            organization_name="Child Care Management System",
            short_name="CCMS",
            address="Not configured",
            is_active=True,
        )
        db.add(profile)
        db.flush()
    original_name = sanitize_filename(file.filename)
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_LOGO_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Logo must be PNG, JPG, JPEG, or WEBP")
    enforce_upload_size(file)
    directory = safe_upload_directory("organization", "branding")
    target = directory / f"organization-logo{extension}"
    with open(target, "wb") as handle:
        file.file.seek(0)
        handle.write(file.file.read())
    profile.logo_path = str(target)
    db.flush()
    return profile


def delete_logo(db: Session) -> OrganizationProfile:
    profile = get_active_profile(db)
    if profile is None or not profile.logo_path:
        raise HTTPException(status_code=404, detail="Organization logo is not configured")
    path = Path(profile.logo_path)
    profile.logo_path = None
    if path.is_file() and settings.upload_path in path.resolve().parents:
        path.unlink()
    db.flush()
    return profile
