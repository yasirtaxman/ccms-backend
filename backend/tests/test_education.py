from datetime import date
from pathlib import Path

from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.child import Child
from app.models.role import Role, UserRole
from app.models.user import User


def make_user(db, username: str, role_name: str) -> User:
    user = User(full_name=f"{username} User", username=username, email=f"{username}@ccms.example", password_hash=hash_password("StrongPassword123!"), is_active=True)
    role = db.query(Role).filter(Role.name == role_name).first() or Role(name=role_name)
    db.add_all([user, role]); db.flush(); db.add(UserRole(user_id=user.id, role_id=role.id)); db.commit(); db.refresh(user)
    return user


def headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.username, 'user_id': user.id})}"}


def make_child(db, code: str) -> Child:
    child = Child(child_id=code, admission_file_no=f"AF-{code}", full_name=f"Child {code}", father_name="Father", grandfather_name="Grandfather", mother_name="Mother", gender="Female", date_of_birth=date(2014, 1, 1), guardian_name="Guardian", guardian_relationship="Aunt", guardian_cnic="42101-1234567-1", guardian_mobile="03001234567", current_address="Address", permanent_address="Address", village_mohallah="Area", union_council="UC", tehsil="Tehsil", district="District", province="Province", admission_date=date(2025, 1, 1), reason_for_admission="Support", status="Active")
    db.add(child); db.commit(); db.refresh(child); return child


def school_payload(code: str) -> dict:
    return {"school_code": code, "school_name": f"School {code}", "school_type": "Government", "phone": "+92 300 1234567", "email": f"{code.lower()}@school.example", "status": "Active"}


def test_school_crud_rbac_delete_and_audit(client, db_session):
    operator = make_user(db_session, "education-operator", "Data Entry Operator")
    viewer = make_user(db_session, "education-viewer", "Viewer")
    admin = make_user(db_session, "education-admin", "Admin")
    auth = headers(operator)
    created = client.post("/schools", json=school_payload("SCH-A"), headers=auth)
    assert created.status_code == 201
    school_id = created.json()["id"]
    assert client.get("/schools", headers=headers(viewer)).status_code == 200
    assert client.get(f"/schools/{school_id}", headers=headers(viewer)).status_code == 200
    assert client.put(f"/schools/{school_id}", json={"city": "Karachi"}, headers=auth).status_code == 200
    assert client.post("/schools", json=school_payload("SCH-B"), headers=headers(viewer)).status_code == 403
    assert client.delete(f"/schools/{school_id}", headers=headers(viewer)).status_code == 403

    empty_school = client.post("/schools", json=school_payload("SCH-EMPTY"), headers=auth).json()
    assert client.delete(f"/schools/{empty_school['id']}", headers=headers(admin)).status_code == 200
    actions = {row.action for row in db_session.query(AuditLog).filter(AuditLog.module == "EDUCATION").all()}
    assert {"SCHOOL_CREATE", "SCHOOL_UPDATE", "SCHOOL_DELETE"} <= actions


def test_education_history_results_attendance_reports_dashboard(client, db_session):
    manager = make_user(db_session, "education-manager", "Manager")
    auth = headers(manager)
    child = make_child(db_session, "EDU-1")
    school = client.post("/schools", json=school_payload("SCH-HISTORY"), headers=auth).json()
    payload = {"school_id": school["id"], "admission_number": "ADM-1", "class_level": "9", "academic_year": "2025-2026", "start_date": "2025-08-01", "status": "Studying"}
    first = client.post(f"/children/{child.id}/education-records", json=payload, headers=auth)
    assert first.status_code == 201
    first_id = first.json()["id"]
    assert client.post(f"/children/{child.id}/education-records", json={**payload, "academic_year": "2026-2027"}, headers=auth).status_code == 409

    dropped = client.put(f"/education-records/{first_id}", json={"status": "Dropped", "end_date": "2026-03-01"}, headers=auth)
    assert dropped.status_code == 200
    second = client.post(f"/children/{child.id}/education-records", json={**payload, "academic_year": "2026-2027", "start_date": "2026-08-01", "class_level": "10"}, headers=auth)
    assert second.status_code == 201
    second_id = second.json()["id"]
    history = client.get(f"/children/{child.id}/education-records", headers=auth).json()
    assert {item["status"] for item in history} == {"Dropped", "Studying"}
    assert client.delete(f"/schools/{school['id']}", headers=headers(make_user(db_session, "history-admin", "Admin"))).status_code == 409

    result = client.post(f"/education-records/{second_id}/results", json={"exam_name": "Board", "exam_date": "2026-11-01", "total_marks": 100, "obtained_marks": 75, "grade": "B"}, headers=auth)
    assert result.status_code == 201
    assert float(result.json()["percentage"]) == 75.0
    updated_result = client.put(f"/results/{result.json()['id']}", json={"obtained_marks": 80}, headers=auth)
    assert float(updated_result.json()["percentage"]) == 80.0

    attendance = client.post(f"/education-records/{second_id}/attendance", json={"month": 9, "year": 2026, "total_days": 20, "present_days": 14, "absent_days": 6}, headers=auth)
    assert attendance.status_code == 201
    assert float(attendance.json()["attendance_percentage"]) == 70.0
    assert client.post(f"/education-records/{second_id}/attendance", json={"month": 9, "year": 2026, "total_days": 20, "present_days": 14, "absent_days": 6}, headers=auth).status_code == 409
    assert client.put(f"/attendance/{attendance.json()['id']}", json={"present_days": 18, "absent_days": 2}, headers=auth).json()["attendance_percentage"] == "90.00"

    assert len(client.get("/reports/top-performers", headers=auth).json()) == 1
    assert len(client.get("/reports/low-attendance", params={"threshold": 95}, headers=auth).json()) == 1
    assert len(client.get("/reports/dropout-students", headers=auth).json()) == 1
    assert len(client.get("/reports/board-exam-students", headers=auth).json()) == 1
    dashboard = client.get("/dashboard/education", headers=auth).json()
    assert dashboard["total_students"] == 1
    assert dashboard["active_students"] == 1
    assert dashboard["board_students"] == 1
    assert dashboard["dropout_students"] == 1
    assert dashboard["average_marks"] == 80.0
    assert dashboard["average_attendance"] == 90.0

    actions = {row.action for row in db_session.query(AuditLog).filter(AuditLog.module == "EDUCATION").all()}
    assert {"EDUCATION_RECORD_CREATE", "EDUCATION_RECORD_UPDATE", "EXAM_RESULT_CREATE", "EXAM_RESULT_UPDATE", "ATTENDANCE_CREATE", "ATTENDANCE_UPDATE"} <= actions


def test_education_document_upload_delete_and_audit(client, db_session):
    manager = make_user(db_session, "education-doc-manager", "Manager")
    viewer = make_user(db_session, "education-doc-viewer", "Viewer")
    admin = make_user(db_session, "education-doc-admin", "Admin")
    child = make_child(db_session, "EDU-DOC")
    auth = headers(manager)
    school = client.post("/schools", json=school_payload("SCH-DOC"), headers=auth).json()
    record = client.post(f"/children/{child.id}/education-records", json={"school_id": school["id"], "class_level": "8", "academic_year": "2025-2026", "start_date": "2025-08-01", "status": "Studying"}, headers=auth).json()

    invalid = client.post("/education-documents/upload", data={"child_id": child.id, "document_type": "Result Card"}, files={"file": ("result.txt", b"invalid", "text/plain")}, headers=auth)
    assert invalid.status_code == 422
    uploaded = client.post("/education-documents/upload", data={"child_id": child.id, "education_record_id": record["id"], "document_type": "Result Card"}, files={"file": ("result.pdf", b"education document", "application/pdf")}, headers=auth)
    assert uploaded.status_code == 201
    document = uploaded.json()
    assert Path(document["file_path"]).exists()
    assert len(client.get(f"/children/{child.id}/education-documents", headers=headers(viewer)).json()) == 1
    assert client.delete(f"/education-documents/{document['id']}", headers=headers(viewer)).status_code == 403
    assert client.delete(f"/education-documents/{document['id']}", headers=headers(admin)).status_code == 200
    assert not Path(document["file_path"]).exists()
    actions = {row.action for row in db_session.query(AuditLog).filter(AuditLog.module == "EDUCATION").all()}
    assert {"EDUCATION_DOCUMENT_UPLOAD", "EDUCATION_DOCUMENT_DELETE"} <= actions
