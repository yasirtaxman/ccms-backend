from datetime import date, timedelta
from pathlib import Path

from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.child import Child
from app.models.role import Role, UserRole
from app.models.user import User


def make_user(db, username: str, role_name: str) -> User:
    user = User(
        full_name=f"{username} User",
        username=username,
        email=f"{username}@ccms.example",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    role = db.query(Role).filter(Role.name == role_name).first() or Role(name=role_name)
    db.add_all([user, role])
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


def make_child(db, code: str) -> Child:
    child = Child(
        child_id=code,
        admission_file_no=f"AF-{code}",
        full_name=f"Child {code}",
        father_name="Father",
        grandfather_name="Grandfather",
        mother_name="Mother",
        gender="Female",
        date_of_birth=date(2015, 1, 1),
        guardian_name="Guardian",
        guardian_relationship="Aunt",
        guardian_cnic="42101-1234567-1",
        guardian_mobile="03001234567",
        current_address="Address",
        permanent_address="Address",
        village_mohallah="Area",
        union_council="UC",
        tehsil="Tehsil",
        district="District",
        province="Province",
        admission_date=date(2025, 1, 1),
        reason_for_admission="Support",
        status="Active",
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


def test_medical_profile_rbac_uniqueness_and_audit(client, db_session):
    manager = make_user(db_session, "medical-manager", "Manager")
    viewer = make_user(db_session, "medical-viewer", "Viewer")
    child = make_child(db_session, "MED-1")
    payload = {
        "blood_group": "A+",
        "allergies": "Peanuts",
        "chronic_diseases": "Asthma",
        "special_needs": "Inhaler access",
        "height_cm": 140.5,
        "weight_kg": 35.2,
    }
    created = client.post(
        f"/children/{child.id}/medical-profile", json=payload, headers=headers(manager)
    )
    assert created.status_code == 201
    assert created.json()["created_by"] == manager.id
    assert client.post(
        f"/children/{child.id}/medical-profile", json=payload, headers=headers(manager)
    ).status_code == 409

    updated = client.put(
        f"/children/{child.id}/medical-profile",
        json={"emergency_notes": "Keep rescue inhaler nearby"},
        headers=headers(manager),
    )
    assert updated.status_code == 200
    assert client.get(
        f"/children/{child.id}/medical-profile", headers=headers(viewer)
    ).status_code == 200

    second_child = make_child(db_session, "MED-2")
    assert client.post(
        f"/children/{second_child.id}/medical-profile", json={}, headers=headers(viewer)
    ).status_code == 403
    actions = [
        row.action
        for row in db_session.query(AuditLog)
        .filter(AuditLog.module == "MEDICAL")
        .order_by(AuditLog.id)
        .all()
    ]
    assert actions == ["MEDICAL_PROFILE_CREATE", "MEDICAL_PROFILE_UPDATE"]


def test_visits_medications_vaccinations_reports_dashboard_and_data_entry(
    client, db_session
):
    operator = make_user(db_session, "medical-operator", "Data Entry Operator")
    auth = headers(operator)
    child = make_child(db_session, "MED-CLINICAL")
    today = date.today()

    visit = client.post(
        f"/children/{child.id}/medical-visits",
        json={
            "visit_date": today.isoformat(),
            "doctor_name": "Dr. Sara Khan",
            "hospital_name": "City Hospital",
            "visit_type": "Routine",
            "symptoms": "Cough",
        },
        headers=auth,
    )
    assert visit.status_code == 201
    assert client.put(
        f"/medical-visits/{visit.json()['id']}",
        json={"diagnosis": "Seasonal allergy", "treatment": "Antihistamine"},
        headers=auth,
    ).status_code == 200

    medication = client.post(
        f"/children/{child.id}/medications",
        json={
            "medicine_name": "Cetirizine",
            "dosage": "5 mg",
            "frequency": "Once daily",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=7)).isoformat(),
            "status": "Active",
        },
        headers=auth,
    )
    assert medication.status_code == 201
    assert client.put(
        f"/medications/{medication.json()['id']}",
        json={"end_date": (today - timedelta(days=1)).isoformat()},
        headers=auth,
    ).status_code == 422
    assert client.put(
        f"/medications/{medication.json()['id']}",
        json={"notes": "Monitor response"},
        headers=auth,
    ).status_code == 200

    vaccination = client.post(
        f"/children/{child.id}/vaccinations",
        json={
            "vaccine_name": "Tetanus",
            "dose_number": 1,
            "vaccination_date": today.isoformat(),
            "next_due_date": (today + timedelta(days=20)).isoformat(),
            "administered_by": "Nurse Amina",
        },
        headers=auth,
    )
    assert vaccination.status_code == 201
    assert client.put(
        f"/vaccinations/{vaccination.json()['id']}",
        json={"remarks": "No adverse reaction"},
        headers=auth,
    ).status_code == 200

    assert client.get("/reports/medical-visits", headers=auth).status_code == 200
    assert len(client.get("/reports/active-medications", headers=auth).json()) == 1
    assert len(client.get("/reports/upcoming-vaccinations", headers=auth).json()) == 1
    dashboard = client.get("/dashboard/medical", headers=auth).json()
    assert dashboard["total_children"] == 1
    assert dashboard["active_medications"] == 1
    assert dashboard["upcoming_vaccinations"] == 1
    assert dashboard["medical_visits_this_month"] == 1

    actions = {
        row.action
        for row in db_session.query(AuditLog).filter(AuditLog.module == "MEDICAL").all()
    }
    assert {
        "MEDICAL_VISIT_CREATE",
        "MEDICAL_VISIT_UPDATE",
        "MEDICATION_CREATE",
        "MEDICATION_UPDATE",
        "VACCINATION_CREATE",
        "VACCINATION_UPDATE",
    } <= actions


def test_medical_document_upload_validation_delete_and_audit(client, db_session):
    manager = make_user(db_session, "document-manager", "Manager")
    viewer = make_user(db_session, "document-viewer", "Viewer")
    admin = make_user(db_session, "document-admin", "Admin")
    child = make_child(db_session, "MED-DOC")
    auth = headers(manager)
    visit = client.post(
        f"/children/{child.id}/medical-visits",
        json={
            "visit_date": date.today().isoformat(),
            "doctor_name": "Dr. Ali",
            "visit_type": "Specialist",
        },
        headers=auth,
    ).json()

    invalid = client.post(
        "/medical-documents/upload",
        data={"child_id": child.id, "document_type": "Prescription"},
        files={"file": ("notes.txt", b"not allowed", "text/plain")},
        headers=auth,
    )
    assert invalid.status_code == 422

    uploaded = client.post(
        "/medical-documents/upload",
        data={
            "child_id": child.id,
            "medical_visit_id": visit["id"],
            "document_type": "Prescription",
        },
        files={"file": ("prescription.pdf", b"medical document", "application/pdf")},
        headers=auth,
    )
    assert uploaded.status_code == 201
    document = uploaded.json()
    assert Path(document["file_path"]).exists()
    assert len(
        client.get(
            f"/children/{child.id}/medical-documents", headers=headers(viewer)
        ).json()
    ) == 1
    assert client.delete(
        f"/medical-documents/{document['id']}", headers=headers(viewer)
    ).status_code == 403
    assert client.delete(
        f"/medical-documents/{document['id']}", headers=headers(admin)
    ).status_code == 200
    assert not Path(document["file_path"]).exists()

    actions = [
        row.action
        for row in db_session.query(AuditLog)
        .filter(AuditLog.module == "MEDICAL")
        .order_by(AuditLog.id)
        .all()
    ]
    assert "MEDICAL_DOCUMENT_UPLOAD" in actions
    assert "MEDICAL_DOCUMENT_DELETE" in actions
