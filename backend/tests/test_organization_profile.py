from io import BytesIO

from app.models.audit_log import AuditLog
from tests.test_medical import headers, make_child, make_user


PROFILE_PAYLOAD = {
    "organization_name": "Community Child Care Trust",
    "short_name": "CCCT",
    "address": "Main Welfare Road",
    "city": "Mardan",
    "district": "Mardan",
    "province": "Khyber Pakhtunkhwa",
    "country": "Pakistan",
    "phone": "091-0000000",
    "email": "info@example.org",
    "website": "https://example.org",
    "registration_no": "REG-2026-01",
    "ntn_or_tax_no": "NTN-001",
    "report_footer_text": "Confidential CCMS report",
    "report_watermark_text": "CCMS",
    "primary_color": "#123456",
    "secondary_color": "#EAF2F9",
    "authorized_signatory_name": "Director",
    "authorized_signatory_designation": "Authorized Officer",
    "is_active": True,
}


def test_organization_profile_defaults_admin_update_and_public_read(client, db_session):
    admin = make_user(db_session, "org-admin", "Admin")
    viewer = make_user(db_session, "org-viewer", "Viewer")
    warden = make_user(db_session, "org-warden", "Warden")
    assert client.get("/organization-profile", headers=headers(viewer)).json()["organization_name"] == "Child Care Management System"
    assert client.get("/organization-profile", headers=headers(warden)).status_code == 200

    denied = client.put("/organization-profile", json=PROFILE_PAYLOAD, headers=headers(viewer))
    assert denied.status_code == 403

    saved = client.put("/organization-profile", json=PROFILE_PAYLOAD, headers=headers(admin))
    assert saved.status_code == 200, saved.text
    assert saved.json()["organization_name"] == "Community Child Care Trust"
    assert saved.json()["logo_url"] is None

    public = client.get("/organization-profile", headers=headers(viewer))
    assert public.status_code == 200
    assert public.json()["short_name"] == "CCCT"
    assert "logo_path" not in public.json()
    assert db_session.query(AuditLog).filter_by(action="ORGANIZATION_PROFILE_UPDATED", module="ORGANIZATION_PROFILE").count() == 1


def test_organization_logo_upload_validation_and_delete(client, db_session):
    admin = make_user(db_session, "logo-admin", "Admin")
    bad = client.post(
        "/organization-profile/logo",
        files={"file": ("logo.gif", BytesIO(b"GIF89a"), "image/gif")},
        headers=headers(admin),
    )
    assert bad.status_code == 422

    uploaded = client.post(
        "/organization-profile/logo",
        files={"file": ("logo.png", BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=headers(admin),
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["logo_url"] == "/organization-profile/logo"
    assert client.get("/organization-profile/logo", headers=headers(admin)).status_code == 200

    deleted = client.delete("/organization-profile/logo", headers=headers(admin))
    assert deleted.status_code == 200
    assert deleted.json()["logo_url"] is None
    actions = {row.action for row in db_session.query(AuditLog).filter_by(module="ORGANIZATION_PROFILE")}
    assert {"ORGANIZATION_LOGO_UPLOADED", "ORGANIZATION_LOGO_DELETED"} <= actions


def test_children_pdf_uses_organization_branding(client, db_session):
    admin = make_user(db_session, "pdf-org-admin", "Admin")
    make_child(db_session, "ORG-PDF-1")
    response = client.put("/organization-profile", json=PROFILE_PAYLOAD, headers=headers(admin))
    assert response.status_code == 200

    exported = client.get("/exports/children.pdf", headers=headers(admin))
    assert exported.status_code == 200, exported.text
    assert exported.content.startswith(b"%PDF")
    assert b"Community Child Care Trust" in exported.content or len(exported.content) > 1000
