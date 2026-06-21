from app.core.security import create_access_token, hash_password
from app.models.child import Child
from app.models.role import Role, UserRole
from app.models.user import User


def auth(db, username="admin", role="Admin"):
    user = User(full_name=username, username=username, email=f"{username}@example.test",
                password_hash=hash_password("StrongPassword123!"), is_active=True)
    role_row = Role(name=role)
    db.add_all([user, role_row]); db.flush()
    db.add(UserRole(user_id=user.id, role_id=role_row.id)); db.commit(); db.refresh(user)
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return user, {"Authorization": f"Bearer {token}"}


def child():
    from datetime import date
    return Child(child_id="CH-1", admission_file_no="ADM-1", full_name="Ali Child",
        father_name="Father", grandfather_name="Grandfather", mother_name="Mother",
        gender="Male", date_of_birth=date(2015, 1, 1), guardian_name="Guardian",
        guardian_relationship="Uncle", guardian_cnic="secret-cnic", guardian_mobile="secret-mobile",
        current_address="secret current address", permanent_address="secret permanent address",
        village_mohallah="Village", union_council="UC", tehsil="Tehsil", district="District",
        province="Province", admission_date=date(2026, 1, 1), reason_for_admission="Care", status="Active")


def test_dashboards_profile_search_and_reports(client, db_session):
    _, headers = auth(db_session)
    record = child(); db_session.add(record); db_session.commit()
    for path in ("/dashboard/executive", "/dashboard/operational", "/dashboard/alerts"):
        assert client.get(path, headers=headers).status_code == 200
    profile = client.get(f"/children/{record.id}/complete-profile-summary", headers=headers)
    assert profile.status_code == 200
    assert "guardian_cnic" not in str(profile.json()).lower()
    assert client.get("/search/global?q=ali", headers=headers).json()["children"][0]["display_title"] == "Ali Child"
    paths = ("children", "sponsorships", "accommodation", "medical", "education", "case-management")
    for name in paths:
        response = client.get(f"/reports/consolidated/{name}?limit=1&offset=0", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["pagination"]["limit"] == 1
    assert client.get("/reports/consolidated/children?limit=501", headers=headers).status_code == 422


def test_viewer_safe_access_and_admin_only_audit(client, db_session):
    _, headers = auth(db_session, "viewer", "Viewer")
    body = client.get("/dashboard/alerts", headers=headers).json()
    assert all(not group["references"] for group in body.values())
    assert client.get("/reports/audit-summary", headers=headers).status_code == 403
    report = client.get("/reports/consolidated/children", headers=headers)
    assert report.status_code == 200
    serialized = report.text.lower()
    assert "guardian_cnic" not in serialized and "address" not in serialized
