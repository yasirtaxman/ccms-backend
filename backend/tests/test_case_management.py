from datetime import date, timedelta

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


def profile_payload(code: str, risk: str = "Low") -> dict:
    return {"case_number": code, "case_opened_date": date.today().isoformat(), "case_status": "Open", "risk_level": risk, "welfare_status": "Stable", "assigned_case_worker": "Case Worker"}


def test_case_profile_lifecycle_closed_protection_and_rbac(client, db_session):
    operator = make_user(db_session, "case-operator", "Data Entry Operator")
    manager = make_user(db_session, "case-manager", "Manager")
    admin = make_user(db_session, "case-admin", "Admin")
    viewer = make_user(db_session, "case-viewer", "Viewer")
    child = make_child(db_session, "CASE-1")
    created = client.post(f"/children/{child.id}/case-profile", json=profile_payload("CASE-0001", "Critical"), headers=headers(operator))
    assert created.status_code == 201
    assert client.post(f"/children/{child.id}/case-profile", json=profile_payload("CASE-0002"), headers=headers(operator)).status_code == 409
    assert client.get(f"/children/{child.id}/case-profile", headers=headers(viewer)).status_code == 200
    assert client.put(f"/children/{child.id}/case-profile", json={"case_summary": "Initial assessment"}, headers=headers(operator)).status_code == 200
    assert client.post(f"/children/{child.id}/case-profile/close", headers=headers(operator)).status_code == 403
    assert client.post(f"/children/{child.id}/case-profile/close", headers=headers(manager)).status_code == 200
    assert client.put(f"/children/{child.id}/case-profile", json={"case_summary": "Blocked"}, headers=headers(operator)).status_code == 403
    assert client.post(f"/children/{child.id}/case-profile/reopen", headers=headers(manager)).status_code == 403
    assert client.post(f"/children/{child.id}/case-profile/reopen", headers=headers(admin)).status_code == 200
    dashboard = client.get("/dashboard/case-management", headers=headers(viewer)).json()
    assert dashboard["critical_risk_children"] == 1
    actions = {row.action for row in db_session.query(AuditLog).filter(AuditLog.module == "CASE_PROFILE").all()}
    assert {"CASE_PROFILE_CREATE", "CASE_PROFILE_UPDATE", "CASE_PROFILE_CLOSE", "CASE_PROFILE_REOPEN"} <= actions


def test_note_visibility_filters_followups_and_soft_delete(client, db_session):
    manager = make_user(db_session, "note-manager", "Manager")
    operator = make_user(db_session, "note-operator", "Data Entry Operator")
    viewer = make_user(db_session, "note-viewer", "Viewer")
    admin = make_user(db_session, "note-admin", "Admin")
    child = make_child(db_session, "NOTE-1")
    profile = client.post(f"/children/{child.id}/case-profile", json=profile_payload("NOTE-CASE"), headers=headers(manager)).json()
    notes = {}
    for visibility in ("Normal", "Confidential", "Restricted"):
        response = client.post(f"/children/{child.id}/case-notes", json={"case_profile_id": profile["id"], "note_date": date.today().isoformat(), "note_type": "General", "title": visibility, "description": f"{visibility} note", "visibility": visibility, "follow_up_required": visibility == "Normal", "follow_up_date": date.today().isoformat() if visibility == "Normal" else None}, headers=headers(manager))
        assert response.status_code == 201; notes[visibility] = response.json()
    assert len(client.get(f"/children/{child.id}/case-notes", headers=headers(viewer)).json()) == 1
    assert len(client.get(f"/children/{child.id}/case-notes", headers=headers(operator)).json()) == 2
    assert len(client.get(f"/children/{child.id}/case-notes", headers=headers(manager)).json()) == 3
    assert client.get(f"/case-notes/{notes['Restricted']['id']}", headers=headers(operator)).status_code == 404
    assert client.post(f"/children/{child.id}/case-notes", json={"note_date": date.today().isoformat(), "note_type": "Legal", "title": "No", "description": "No", "visibility": "Restricted"}, headers=headers(operator)).status_code == 403
    assert client.put(f"/case-notes/{notes['Normal']['id']}", json={"description": "Updated"}, headers=headers(operator)).status_code == 200
    assert len(client.get("/reports/pending-follow-ups", headers=headers(viewer)).json()) == 1
    assert client.delete(f"/case-notes/{notes['Normal']['id']}", headers=headers(viewer)).status_code == 403
    assert client.delete(f"/case-notes/{notes['Normal']['id']}", headers=headers(admin)).status_code == 200
    assert client.get(f"/case-notes/{notes['Normal']['id']}", headers=headers(manager)).status_code == 404


def test_counseling_incidents_plans_reviews_reports_dashboard_and_audit(client, db_session):
    operator = make_user(db_session, "workflow-operator", "Data Entry Operator")
    manager = make_user(db_session, "workflow-manager", "Manager")
    admin = make_user(db_session, "workflow-admin", "Admin")
    auth = headers(operator); today = date.today(); child = make_child(db_session, "FLOW-1")
    profile = client.post(f"/children/{child.id}/case-profile", json=profile_payload("FLOW-CASE", "High"), headers=auth).json()

    session = client.post(f"/children/{child.id}/counseling-sessions", json={"session_date": today.isoformat(), "counselor_name": "Counselor A", "session_type": "Individual", "status": "Scheduled", "next_session_date": (today + timedelta(days=5)).isoformat()}, headers=auth)
    assert session.status_code == 201
    assert client.put(f"/counseling-sessions/{session.json()['id']}", json={"observations": "Progressing"}, headers=auth).status_code == 200

    incident = client.post(f"/children/{child.id}/incidents", json={"incident_date": today.isoformat(), "incident_type": "Safety", "severity": "Critical", "description": "Safety incident", "reported_by": "Case Worker"}, headers=auth)
    assert incident.status_code == 201
    assert client.post(f"/incidents/{incident.json()['id']}/review", json={}, headers=auth).status_code == 403
    assert client.post(f"/incidents/{incident.json()['id']}/review", json={}, headers=headers(manager)).json()["review_status"] == "Reviewed"
    assert client.post(f"/incidents/{incident.json()['id']}/close", json={}, headers=headers(manager)).json()["review_status"] == "Closed"

    plan_payload = {"case_profile_id": profile["id"], "plan_title": "Education plan", "plan_start_date": today.isoformat(), "goal_area": "Education", "goals": "Improve school progress", "status": "Active"}
    plan = client.post(f"/children/{child.id}/care-plans", json=plan_payload, headers=auth)
    assert plan.status_code == 201
    assert client.post(f"/children/{child.id}/care-plans", json={**plan_payload, "plan_title": "Duplicate"}, headers=auth).status_code == 409
    assert client.post(f"/care-plans/{plan.json()['id']}/complete", headers=auth).json()["status"] == "Completed"
    second_plan = client.post(f"/children/{child.id}/care-plans", json={**plan_payload, "plan_title": "Replacement"}, headers=auth).json()
    assert client.post(f"/care-plans/{second_plan['id']}/cancel", headers=auth).json()["status"] == "Cancelled"

    review = client.post(f"/children/{child.id}/case-reviews", json={"case_profile_id": profile["id"], "review_date": today.isoformat(), "review_type": "Monthly", "next_review_date": (today + timedelta(days=10)).isoformat(), "status": "Pending"}, headers=auth)
    assert review.status_code == 201
    assert client.put(f"/case-reviews/{review.json()['id']}", json={"summary": "Monthly review"}, headers=auth).status_code == 200

    assert len(client.get("/reports/high-risk-children", headers=auth).json()) == 1
    assert len(client.get("/reports/critical-incidents", headers=auth).json()) == 1
    assert len(client.get("/reports/upcoming-case-reviews", headers=auth).json()) == 1
    assert len(client.get("/reports/upcoming-counseling-sessions", headers=auth).json()) == 1
    dashboard = client.get("/dashboard/case-management", headers=auth).json()
    assert dashboard["high_risk_children"] == 1
    assert dashboard["upcoming_case_reviews"] == 1
    assert dashboard["upcoming_counseling_sessions"] == 1

    assert client.delete(f"/counseling-sessions/{session.json()['id']}", headers=headers(admin)).status_code == 200
    assert client.delete(f"/incidents/{incident.json()['id']}", headers=headers(admin)).status_code == 200
    assert client.delete(f"/care-plans/{second_plan['id']}", headers=headers(admin)).status_code == 200
    assert client.delete(f"/case-reviews/{review.json()['id']}", headers=headers(admin)).status_code == 200
    actions = {row.action for row in db_session.query(AuditLog).all()}
    required = {"COUNSELING_SESSION_CREATE", "COUNSELING_SESSION_UPDATE", "COUNSELING_SESSION_DELETE", "INCIDENT_CREATE", "INCIDENT_REVIEW", "INCIDENT_CLOSE", "INCIDENT_DELETE", "CARE_PLAN_CREATE", "CARE_PLAN_COMPLETE", "CARE_PLAN_CANCEL", "CARE_PLAN_DELETE", "CASE_REVIEW_CREATE", "CASE_REVIEW_UPDATE", "CASE_REVIEW_DELETE"}
    assert required <= actions
