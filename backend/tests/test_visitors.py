from datetime import date
from app.models.audit_log import AuditLog
from tests.test_medical import headers,make_child,make_user

VISITOR={"visitor_code":"VIS-001","full_name":"Ahmed Visitor","father_name":"Father","cnic_passport":"12345-1234567-1","mobile":"03001234567","relationship_to_child":"Uncle","district":"Mardan","province":"Khyber Pakhtunkhwa","status":"Pending Verification"}

def test_visitor_crud_verification_privacy_and_actions(client,db_session):
    admin=make_user(db_session,"visitor-admin","Admin");viewer=make_user(db_session,"visitor-viewer","Viewer");auth=headers(admin)
    created=client.post("/visitors",json=VISITOR,headers=auth);assert created.status_code==201,created.text;visitor_id=created.json()["id"]
    assert client.put(f"/visitors/{visitor_id}",json={"district":"Peshawar"},headers=auth).status_code==200
    safe=client.get(f"/visitors/{visitor_id}",headers=headers(viewer));assert safe.status_code==200;assert "cnic_passport" not in safe.json() and "mobile" not in safe.json()
    verified=client.post(f"/visitors/{visitor_id}/verify",json={"verification_method":"Original CNIC"},headers=auth);assert verified.status_code==200 and verified.json().get("is_verified"),verified.text
    assert client.post(f"/visitors/{visitor_id}/block",headers=auth).json()["status"]=="Blocked"
    assert client.post(f"/visitors/{visitor_id}/activate",headers=auth).json()["status"]=="Active"
    actions={row.action for row in db_session.query(AuditLog).filter_by(module="VISITORS")};assert {"VISITOR_CREATED","VISITOR_UPDATED","VISITOR_VERIFIED","VISITOR_BLOCKED","VISITOR_ACTIVATED"}<=actions

def test_child_visit_workflow_warden_permissions_and_exports(client,db_session):
    admin=make_user(db_session,"visit-admin","Admin");manager=make_user(db_session,"visit-manager","Manager");warden=make_user(db_session,"visit-warden","Warden");child=make_child(db_session,"VISIT-CHILD");admin_auth=headers(admin)
    visitor=client.post("/visitors",json={**VISITOR,"visitor_code":"VIS-002"},headers=admin_auth).json();client.post(f"/visitors/{visitor['id']}/verify",json={"verification_method":"Original CNIC"},headers=admin_auth)
    payload={"visit_code":"MEET-001","child_id":child.id,"visitor_id":visitor["id"],"visit_date":date.today().isoformat(),"meeting_purpose":"Family Visit","meeting_location":"Visitor Room"}
    created=client.post("/child-visits",json=payload,headers=headers(warden));assert created.status_code==201,created.text;visit_id=created.json()["id"]
    assert client.post(f"/child-visits/{visit_id}/approve",headers=headers(warden)).status_code==403
    assert client.post(f"/child-visits/{visit_id}/check-in",json={},headers=headers(warden)).status_code==409
    approved=client.post(f"/child-visits/{visit_id}/approve",headers=headers(manager));assert approved.status_code==200,approved.text
    checked=client.post(f"/child-visits/{visit_id}/check-in",json={"check_in_time":"09:00:00"},headers=headers(warden));assert checked.status_code==200 and checked.json()["visit_status"]=="Checked In"
    early=client.post(f"/child-visits/{visit_id}/check-out",json={"check_out_time":"08:59:00"},headers=headers(warden));assert early.status_code==422
    completed=client.post(f"/child-visits/{visit_id}/check-out",json={"check_out_time":"10:00:00"},headers=headers(warden));assert completed.status_code==200 and completed.json()["visit_status"]=="Completed"
    assert client.get(f"/children/{child.id}/visits",headers=headers(warden)).status_code==200
    assert client.get("/users",headers=headers(warden)).status_code==403
    for path in ("visitors.pdf","child-visits.pdf",f"daily-visitor-register.pdf?date={date.today().isoformat()}",f"monthly-visitor-register.pdf?month={date.today().month}&year={date.today().year}"):
        response=client.get(f"/exports/{path}",headers=admin_auth);assert response.status_code==200,response.text;assert response.content.startswith(b"%PDF")
    actions={row.action for row in db_session.query(AuditLog).filter_by(module="CHILD_VISITS")};assert {"CHILD_VISIT_CREATED","CHILD_VISIT_APPROVED","CHILD_VISIT_CHECKED_IN","CHILD_VISIT_CHECKED_OUT"}<=actions

def test_permission_admin_matrix_and_admin_protection(client,db_session):
    admin=make_user(db_session,"permission-admin","Admin");auth=headers(admin)
    created=client.post("/roles",json={"name":"Visitor Desk"},headers=auth);assert created.status_code==201,created.text;role_id=created.json()["id"]
    permissions=client.get("/permissions",headers=auth).json();selected=[item["id"] for item in permissions if item["name"] in {"visitors.view","child_visits.view"}]
    replaced=client.put(f"/roles/{role_id}/permissions",json={"permission_ids":selected},headers=auth);assert replaced.status_code==200 and {item["name"] for item in replaced.json()}=={"visitors.view","child_visits.view"}
    admin_role=next(role for role in client.get("/roles",headers=auth).json() if role["name"]=="Admin")
    assert client.put(f"/roles/{admin_role['id']}/permissions",json={"permission_ids":[]},headers=auth).status_code==409
    assert client.delete(f"/roles/{admin_role['id']}",headers=auth).status_code==409
