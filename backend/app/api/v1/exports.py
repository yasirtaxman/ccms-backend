from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.deps import can_operational_read, get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services import report_service
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.excel_service import build_excel_report,build_full_profile_excel
from app.services.pdf_service import build_pdf_report,build_full_profile_pdf,build_attendance_pdf
from app.services.profile_export_service import build_full_child_profile
from app.services.organization_profile_service import report_branding
from app.api.v1.child_attendance import daily_report, monthly_report
from app.core.config import settings

router=APIRouter(prefix="/exports",tags=["Exports"])
REPORTS={"children":report_service.children_report,"sponsors":report_service.sponsors_report,"sponsorships":report_service.sponsorships_report,"accommodation":report_service.accommodation_report,"medical":report_service.medical_report,"education":report_service.education_report,"case-management":report_service.case_report}
def export(db,user,name,kind):
    report=REPORTS[name](db,user.username,limit=settings.EXPORT_MAX_ROWS,offset=0); rows=report.data
    stream=build_excel_report(name.replace("-"," ").title(),rows,user.username,report.filters_applied) if kind=="xlsx" else build_pdf_report(name.replace("-"," ").title(),rows,user.username,report.filters_applied,report_branding(db))
    add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL if kind=="xlsx" else AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":name,"filters":report.filters_applied}); db.commit()
    media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if kind=="xlsx" else "application/pdf"
    return StreamingResponse(stream,media_type=media,headers={"Content-Disposition":f'attachment; filename="ccms-{name}.{kind}"'})
for name in REPORTS:
    def make(n,k):
        def endpoint(db:Session=Depends(get_db),user:User=Depends(can_operational_read)): return export(db,user,n,k)
        return endpoint
    router.add_api_route(f"/{name}.xlsx",make(name,"xlsx"),methods=["GET"])
    router.add_api_route(f"/{name}.pdf",make(name,"pdf"),methods=["GET"])

def profile_export(child_id,kind,db,user):
    profile=build_full_child_profile(db,child_id,{role.name for role in user.roles})
    stream=build_full_profile_excel(profile,user.username) if kind=="xlsx" else build_full_profile_pdf(profile,user.username,report_branding(db))
    add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL if kind=="xlsx" else AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,record_id=child_id,new_values={"report_type":"full-child-profile"}); db.commit()
    media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if kind=="xlsx" else "application/pdf"; return StreamingResponse(stream,media_type=media,headers={"Content-Disposition":f'attachment; filename="ccms-child-{child_id}.{kind}"'})
@router.get("/full-child-profile/{child_id}.xlsx")
def profile_xlsx(child_id:int,db:Session=Depends(get_db),user:User=Depends(can_operational_read)): return profile_export(child_id,"xlsx",db,user)
@router.get("/full-child-profile/{child_id}.pdf")
def profile_pdf(child_id:int,db:Session=Depends(get_db),user:User=Depends(can_operational_read)): return profile_export(child_id,"pdf",db,user)

DAILY_COLUMNS=[("child_code","Child ID"),("child_name","Child Name"),("gender","Gender"),("district","District"),("room_name","Room"),("bed_code","Bed"),("status","Attendance Status"),("check_in_time","Check In"),("check_out_time","Check Out"),("remarks","Remarks")]
MONTHLY_COLUMNS=[("child_code","Child ID"),("child_name","Child Name"),("gender","Gender"),("district","District"),("present_days","Present Days"),("absent_days","Absent Days"),("leave_days","Leave Days"),("medical_leave_days","Medical Leave Days"),("home_visit_days","Home Visit Days"),("unauthorized_absence_days","Unauthorized Absence Days"),("missing_days","Missing Days"),("attendance_percentage","Attendance %")]

@router.get("/daily-attendance.pdf")
def daily_attendance_pdf(date_filter:date|None=Query(None,alias="date"),from_date:date|None=None,to_date:date|None=None,status_filter:str|None=Query(None,alias="status"),db:Session=Depends(get_db),user:User=Depends(can_operational_read)):
    if date_filter:from_date=to_date=date_filter
    rows=daily_report(from_date,to_date,status_filter,None,None,None,db,user);period=str(date_filter or f"{from_date or 'Beginning'} to {to_date or 'Today'}")
    stream=build_attendance_pdf("Daily Child Attendance Report",rows,user.username,period,DAILY_COLUMNS,report_branding(db));add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":"daily-attendance","period":period});db.commit()
    return StreamingResponse(stream,media_type="application/pdf",headers={"Content-Disposition":'attachment; filename="ccms-daily-attendance.pdf"'})

@router.get("/monthly-child-attendance.pdf")
def monthly_attendance_pdf(month:int=Query(...,ge=1,le=12),year:int=Query(...,ge=2000,le=2100),child_id:int|None=None,db:Session=Depends(get_db),user:User=Depends(can_operational_read)):
    rows=monthly_report(month,year,child_id,db,user);period=f"{year}-{month:02d}"
    stream=build_attendance_pdf("Monthly Child Attendance Report",rows,user.username,period,MONTHLY_COLUMNS,report_branding(db));add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":"monthly-child-attendance","period":period,"child_id":child_id});db.commit()
    return StreamingResponse(stream,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="ccms-monthly-attendance-{period}.pdf"'})

@router.get("/daily-attendance.xlsx")
def daily_attendance_excel(date_filter:date|None=Query(None,alias="date"),from_date:date|None=None,to_date:date|None=None,status_filter:str|None=Query(None,alias="status"),db:Session=Depends(get_db),user:User=Depends(can_operational_read)):
    if date_filter:from_date=to_date=date_filter
    rows=daily_report(from_date,to_date,status_filter,None,None,None,db,user);stream=build_excel_report("Daily Child Attendance",rows,user.username,{"from_date":from_date,"to_date":to_date,"status":status_filter});add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":"daily-attendance"});db.commit()
    return StreamingResponse(stream,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":'attachment; filename="ccms-daily-attendance.xlsx"'})

@router.get("/monthly-child-attendance.xlsx")
def monthly_attendance_excel(month:int=Query(...,ge=1,le=12),year:int=Query(...,ge=2000,le=2100),child_id:int|None=None,db:Session=Depends(get_db),user:User=Depends(can_operational_read)):
    rows=monthly_report(month,year,child_id,db,user);stream=build_excel_report("Monthly Child Attendance",rows,user.username,{"month":month,"year":year,"child_id":child_id});add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":"monthly-child-attendance"});db.commit()
    return StreamingResponse(stream,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="ccms-monthly-attendance-{year}-{month:02d}.xlsx"'})

def admin_export(db,user,name,kind,rows):
    stream=build_excel_report(name,rows,user.username,{}) if kind=="xlsx" else build_pdf_report(name,rows,user.username,{},report_branding(db))
    add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL if kind=="xlsx" else AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":name.lower().replace(" ","-")});db.commit()
    media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if kind=="xlsx" else "application/pdf"
    return StreamingResponse(stream,media_type=media,headers={"Content-Disposition":f'attachment; filename="ccms-{name.lower().replace(" ","-")}.{kind}"'})

def user_rows(db):return [{"id":row.id,"username":row.username,"full_name":row.full_name,"email":row.email,"is_active":row.is_active,"force_password_change":row.force_password_change,"created_at":row.created_at} for row in db.scalars(select(User).order_by(User.username)).all()]
def audit_rows(db):return [{"id":row.id,"user_id":row.user_id,"action":row.action,"module":row.module,"record_id":row.record_id,"created_at":row.created_at} for row in db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5000)).all()]

@router.get("/users.pdf")
def users_pdf(db:Session=Depends(get_db),user:User=Depends(require_admin)):return admin_export(db,user,"Users","pdf",user_rows(db))
@router.get("/users.xlsx")
def users_excel(db:Session=Depends(get_db),user:User=Depends(require_admin)):return admin_export(db,user,"Users","xlsx",user_rows(db))
@router.get("/audit-summary.pdf")
def audit_pdf(db:Session=Depends(get_db),user:User=Depends(require_admin)):return admin_export(db,user,"Audit Summary","pdf",audit_rows(db))
@router.get("/audit-summary.xlsx")
def audit_excel(db:Session=Depends(get_db),user:User=Depends(require_admin)):return admin_export(db,user,"Audit Summary","xlsx",audit_rows(db))
