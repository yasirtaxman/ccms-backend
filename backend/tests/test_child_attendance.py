from datetime import date
from app.models.audit_log import AuditLog
from tests.test_medical import headers,make_child,make_user

def payload(status="Present",attendance_date=None):
    return {"attendance_date":(attendance_date or date.today()).isoformat(),"status":status,"check_in_time":"08:00:00","check_out_time":"17:00:00","remarks":"Daily presence"}

def test_daily_attendance_crud_reports_dashboard_and_audit(client,db_session):
    manager=make_user(db_session,"attendance-manager","Manager");admin=make_user(db_session,"attendance-admin","Admin");child=make_child(db_session,"ATT-1");auth=headers(manager)
    created=client.post(f"/children/{child.id}/daily-attendance",json=payload(),headers=auth);assert created.status_code==201,created.text
    attendance_id=created.json()["id"]
    assert client.post(f"/children/{child.id}/daily-attendance",json=payload(),headers=auth).status_code==409
    history=client.get(f"/children/{child.id}/daily-attendance",headers=auth);assert history.status_code==200 and len(history.json())==1
    listed=client.get(f"/daily-attendance?date={date.today().isoformat()}",headers=auth);assert listed.status_code==200 and listed.json()["total"]==1
    updated=client.put(f"/daily-attendance/{attendance_id}",json={"status":"Medical Leave","check_in_time":None,"check_out_time":None,"remarks":"Clinic"},headers=auth);assert updated.status_code==200
    invalid=client.put(f"/daily-attendance/{attendance_id}",json={"status":"Present","check_in_time":"17:00","check_out_time":"08:00"},headers=auth);assert invalid.status_code==422
    today=client.get("/daily-attendance/today",headers=auth).json();assert today["today_medical_leave"]==1 and today["attendance_pending_today"]==0
    dashboard=client.get("/dashboard/daily-attendance",headers=auth);assert dashboard.status_code==200 and dashboard.json()["today_medical_leave"]==1
    assert client.get("/reports/daily-attendance",headers=auth).status_code==200
    monthly=client.get(f"/reports/monthly-child-attendance?month={date.today().month}&year={date.today().year}",headers=auth);assert monthly.status_code==200 and monthly.json()[0]["medical_leave_days"]==1
    deleted=client.delete(f"/daily-attendance/{attendance_id}",headers=headers(admin));assert deleted.status_code==200
    assert client.get("/daily-attendance",headers=auth).json()["total"]==0
    actions={row.action for row in db_session.query(AuditLog).filter_by(module="DAILY_ATTENDANCE")};assert {"DAILY_ATTENDANCE_CREATE","DAILY_ATTENDANCE_UPDATE","DAILY_ATTENDANCE_DELETE"}<=actions

def test_bulk_mark_upsert_validation_rbac_and_alerts(client,db_session):
    operator=make_user(db_session,"attendance-operator","Data Entry Operator");viewer=make_user(db_session,"attendance-viewer","Viewer");child1=make_child(db_session,"ATT-B1");child2=make_child(db_session,"ATT-B2");auth=headers(operator);target=date.today().isoformat()
    request={"attendance_date":target,"records":[{"child_id":child1.id,"status":"Present"},{"child_id":child2.id,"status":"Missing","remarks":"Escalated"}]}
    first=client.post("/daily-attendance/bulk-mark",json=request,headers=auth);assert first.status_code==200 and first.json()["created_count"]==2
    request["records"][0]["status"]="Unauthorized Absence"
    second=client.post("/daily-attendance/bulk-mark",json=request,headers=auth);assert second.status_code==200 and second.json()["updated_count"]==2
    unknown=client.post("/daily-attendance/bulk-mark",json={"attendance_date":target,"records":[{"child_id":999999,"status":"Present"}]},headers=auth);assert unknown.status_code==422
    duplicate=client.post("/daily-attendance/bulk-mark",json={"attendance_date":target,"records":[{"child_id":child1.id,"status":"Present"},{"child_id":child1.id,"status":"Absent"}]},headers=auth);assert duplicate.status_code==422
    viewer_headers=headers(viewer);assert client.get("/daily-attendance/today",headers=viewer_headers).status_code==200
    assert client.post("/daily-attendance/bulk-mark",json=request,headers=viewer_headers).status_code==403
    alerts=client.get("/dashboard/alerts",headers=viewer_headers).json();assert alerts["critical_alerts"]["counts"]["children_missing_today"]==1;assert alerts["warning_alerts"]["counts"]["unauthorized_absences_today"]==1
    assert db_session.query(AuditLog).filter_by(action="DAILY_ATTENDANCE_BULK_MARK").count()==2
