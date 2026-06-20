from datetime import date, timedelta

from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.child import Child
from app.models.role import Role, UserRole
from app.models.sponsor import ChildSponsorship
from app.models.user import User


def make_user(db, username: str, role_name: str) -> User:
    user = User(
        full_name=f"{username} User",
        username=username,
        email=f"{username}@ccms.example",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


def sponsor_payload(code: str = "SP-0001") -> dict:
    return {
        "sponsor_code": code,
        "sponsor_type": "Individual",
        "full_name": "Ayesha Khan",
        "mobile": "+92 300 1234567",
        "email": "ayesha@ccms.example",
        "city": "Karachi",
        "country": "Pakistan",
        "status": "Active",
    }


def make_child(db, code: str = "CH-0001") -> Child:
    child = Child(
        child_id=code,
        admission_file_no=f"AF-{code}",
        full_name="Test Child",
        father_name="Father",
        grandfather_name="Grandfather",
        mother_name="Mother",
        gender="Female",
        date_of_birth=date(2015, 1, 1),
        guardian_name="Guardian",
        guardian_relationship="Uncle",
        guardian_cnic="42101-1234567-1",
        guardian_mobile="03001234567",
        current_address="Current address",
        permanent_address="Permanent address",
        village_mohallah="Area",
        union_council="UC-1",
        tehsil="Tehsil",
        district="District",
        province="Province",
        admission_date=date(2025, 1, 1),
        reason_for_admission="Child welfare support",
        status="Active",
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


def test_sponsor_crud_search_audit_and_soft_delete(client, db_session):
    manager = make_user(db_session, "sponsor-manager", "Manager")
    manager_headers = headers_for(manager)

    created = client.post("/sponsors", json=sponsor_payload(), headers=manager_headers)
    assert created.status_code == 201
    sponsor = created.json()
    assert sponsor["sponsor_code"] == "SP-0001"
    assert sponsor["created_by"] == manager.id

    duplicate = client.post("/sponsors", json=sponsor_payload(), headers=manager_headers)
    assert duplicate.status_code == 409

    searched = client.get(
        "/sponsors/search", params={"name": "Ayesha", "status": "Active"}, headers=manager_headers
    )
    assert searched.status_code == 200
    assert searched.json()["total"] == 1

    updated = client.put(
        f"/sponsors/{sponsor['id']}",
        json={"organization_name": "Community Support Group", "remarks": "Verified"},
        headers=manager_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["organization_name"] == "Community Support Group"

    viewer = make_user(db_session, "sponsor-viewer", "Viewer")
    viewer_headers = headers_for(viewer)
    assert client.get(f"/sponsors/{sponsor['id']}", headers=viewer_headers).status_code == 200
    viewer_result = client.get(f"/sponsors/{sponsor['id']}", headers=viewer_headers).json()
    for sensitive_field in ("cnic_passport", "email", "mobile", "alternate_mobile", "address"):
        assert sensitive_field not in viewer_result
    assert client.get(
        "/sponsors/search", params={"email": "ayesha@ccms.example"}, headers=viewer_headers
    ).status_code == 403
    assert client.post("/sponsors", json=sponsor_payload("SP-0002"), headers=viewer_headers).status_code == 403

    admin = make_user(db_session, "sponsor-admin", "Admin")
    deleted = client.delete(f"/sponsors/{sponsor['id']}", headers=headers_for(admin))
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "Active"
    assert deleted.json()["deleted_at"] is not None
    assert deleted.json()["deleted_by"] == admin.id
    assert client.get(f"/sponsors/{sponsor['id']}", headers=manager_headers).status_code == 404

    actions = {
        row.action
        for row in db_session.query(AuditLog)
        .filter(AuditLog.module == "SPONSORS", AuditLog.record_id == sponsor["id"])
        .all()
    }
    assert actions == {"CREATE", "UPDATE", "DELETE"}


def test_data_entry_can_create_update_and_view_sponsors(client, db_session):
    operator = make_user(db_session, "sponsor-operator", "Data Entry Operator")
    headers = headers_for(operator)
    created = client.post("/sponsors", json=sponsor_payload(), headers=headers)
    assert created.status_code == 201
    sponsor_id = created.json()["id"]
    assert client.get("/sponsors", headers=headers).status_code == 200
    assert client.put(f"/sponsors/{sponsor_id}", json={"city": "Lahore"}, headers=headers).status_code == 200
    assert client.delete(f"/sponsors/{sponsor_id}", headers=headers).status_code == 403


def test_sponsorship_history_validation_reports_and_audit(client, db_session):
    manager = make_user(db_session, "history-manager", "Manager")
    headers = headers_for(manager)
    child = make_child(db_session)
    sponsor = client.post("/sponsors", json=sponsor_payload(), headers=headers).json()

    payload = {
        "sponsor_id": sponsor["id"],
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat(),
        "status": "Active",
        "sponsorship_type": "Education",
        "notes": "School support",
    }
    assert client.post("/children/99999/sponsorships", json=payload, headers=headers).status_code == 404
    invalid_sponsor = {**payload, "sponsor_id": 99999}
    assert client.post(f"/children/{child.id}/sponsorships", json=invalid_sponsor, headers=headers).status_code == 404

    created = client.post(f"/children/{child.id}/sponsorships", json=payload, headers=headers)
    assert created.status_code == 201
    sponsorship_id = created.json()["id"]

    overlapping = {**payload, "start_date": (date.today() + timedelta(days=10)).isoformat()}
    assert client.post(
        f"/children/{child.id}/sponsorships", json=overlapping, headers=headers
    ).status_code == 409

    child_history = client.get(f"/children/{child.id}/sponsorships", headers=headers)
    assert child_history.status_code == 200
    assert [item["id"] for item in child_history.json()] == [sponsorship_id]

    sponsor_children = client.get(f"/sponsors/{sponsor['id']}/children", headers=headers)
    assert sponsor_children.status_code == 200
    assert sponsor_children.json()[0]["child_code"] == child.child_id

    changed = client.put(
        f"/sponsorships/{sponsorship_id}",
        json={"status": "Completed", "notes": "Completed successfully"},
        headers=headers,
    )
    assert changed.status_code == 200
    assert changed.json()["status"] == "Completed"
    assert client.put(
        f"/sponsorships/{sponsorship_id}",
        json={"sponsor_id": sponsor["id"]},
        headers=headers,
    ).status_code == 422

    assert client.get("/reports/sponsors", headers=headers).status_code == 200
    assert client.get("/reports/active-sponsorships", headers=headers).json() == []
    assert client.get("/reports/expired-sponsorships", headers=headers).status_code == 200
    assert len(client.get("/reports/children-without-sponsors", headers=headers).json()) == 1

    logs = db_session.query(AuditLog).filter(
        AuditLog.module == "SPONSORSHIPS", AuditLog.record_id == sponsorship_id
    ).all()
    assert [log.action for log in logs] == ["CREATE", "SPONSORSHIP_STATUS_CHANGE"]
    assert db_session.get(ChildSponsorship, sponsorship_id) is not None


def test_invalid_sponsor_and_sponsorship_values_are_rejected(client, db_session):
    manager = make_user(db_session, "validation-manager", "Manager")
    headers = headers_for(manager)
    invalid_mobile = {**sponsor_payload(), "mobile": "abc"}
    assert client.post("/sponsors", json=invalid_mobile, headers=headers).status_code == 422
    invalid_type = {**sponsor_payload(), "sponsor_type": "Unknown"}
    assert client.post("/sponsors", json=invalid_type, headers=headers).status_code == 422

    child = make_child(db_session)
    sponsor = client.post("/sponsors", json=sponsor_payload(), headers=headers).json()
    invalid_dates = {
        "sponsor_id": sponsor["id"],
        "start_date": "2026-02-01",
        "end_date": "2026-01-01",
        "sponsorship_type": "Full",
    }
    assert client.post(f"/children/{child.id}/sponsorships", json=invalid_dates, headers=headers).status_code == 422
