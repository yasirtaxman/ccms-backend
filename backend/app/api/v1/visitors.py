from datetime import UTC,date,datetime
from fastapi import APIRouter,Depends,HTTPException,Query,status
from fastapi.responses import StreamingResponse
from sqlalchemy import func,or_,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.deps import get_db,require_permission
from app.models.child import Child
from app.models.user import User
from app.models.visitor import ChildVisit,Visitor
from app.schemas.visitors import ChildVisitCreate,ChildVisitResponse,ChildVisitUpdate,VisitCheckInRequest,VisitCheckOutRequest,VisitorCreate,VisitorDashboardResponse,VisitorUpdate,VisitorVerifyRequest
from app.services.audit import AuditAction,AuditModule,add_audit_log
from app.services.excel_service import build_excel_report
from app.services.pdf_service import build_pdf_report
from app.services.organization_profile_service import report_branding
from app.services.permission_service import has_permission
from app.services.visitor_service import base_visit_query,daily_rows,monthly_rows,report_projection,roles,visit_or_404,visit_rows,visitor_or_404,visitor_visible

router=APIRouter(tags=["Visitors and Child Meetings"])
def snap(item):return {column.name:getattr(item,column.name) for column in item.__table__.columns}
def audit(db,user,action,module,item,old=None):add_audit_log(db,user_id=user.id,action=action,module=module,record_id=item.id,old_values=old,new_values=snap(item))

@router.get("/visitors")
def list_visitors(search:str|None=None,status_filter:str|None=Query(None,alias="status"),verified:bool|None=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.view"))):
    stmt=select(Visitor).where(Visitor.deleted_at.is_(None))
    if search:stmt=stmt.where(or_(Visitor.visitor_code.ilike(f"%{search}%"),Visitor.full_name.ilike(f"%{search}%")))
    if status_filter:stmt=stmt.where(Visitor.status==status_filter)
    if verified is not None:stmt=stmt.where(Visitor.is_verified==verified)
    return [visitor_visible(item,user) for item in db.scalars(stmt.order_by(Visitor.full_name).offset(offset).limit(limit)).all()]
@router.post("/visitors",status_code=201)
def create_visitor(payload:VisitorCreate,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.create"))):
    item=Visitor(**payload.model_dump(),created_by_user_id=user.id,updated_by_user_id=user.id);db.add(item)
    try:db.flush();audit(db,user,AuditAction.VISITOR_CREATED,AuditModule.VISITORS,item);db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,"Visitor code already exists")
    db.refresh(item);return visitor_visible(item,user)
@router.get("/visitors/{visitor_id}")
def get_visitor(visitor_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.view"))):return visitor_visible(visitor_or_404(db,visitor_id),user)
@router.put("/visitors/{visitor_id}")
def update_visitor(visitor_id:int,payload:VisitorUpdate,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.update"))):
    item=visitor_or_404(db,visitor_id);old=snap(item)
    for key,value in payload.model_dump(exclude_unset=True).items():setattr(item,key,value)
    item.updated_by_user_id=user.id;item.updated_at=datetime.now(UTC);audit(db,user,AuditAction.VISITOR_UPDATED,AuditModule.VISITORS,item,old);db.commit();return visitor_visible(item,user)
@router.delete("/visitors/{visitor_id}")
def delete_visitor(visitor_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.delete"))):
    item=visitor_or_404(db,visitor_id)
    if db.scalar(select(ChildVisit.id).where(ChildVisit.visitor_id==item.id,ChildVisit.visit_status.in_(["Scheduled","Checked In"])).limit(1)):raise HTTPException(409,"Visitor has an active child visit")
    old=snap(item);item.status="Inactive";item.deleted_at=datetime.now(UTC);item.deleted_by_user_id=user.id;item.updated_by_user_id=user.id;audit(db,user,AuditAction.VISITOR_DEACTIVATED,AuditModule.VISITORS,item,old);db.commit();return {"message":"Visitor deactivated"}
@router.post("/visitors/{visitor_id}/verify")
def verify(visitor_id:int,payload:VisitorVerifyRequest,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.verify"))):
    item=visitor_or_404(db,visitor_id);old=snap(item);item.is_verified=True;item.verification_method=payload.verification_method;item.verified_by_user_id=user.id;item.verified_at=datetime.now(UTC);item.status="Active";item.updated_by_user_id=user.id;audit(db,user,AuditAction.VISITOR_VERIFIED,AuditModule.VISITORS,item,old);db.commit();return visitor_visible(item,user)
@router.post("/visitors/{visitor_id}/block")
def block(visitor_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.block"))):
    item=visitor_or_404(db,visitor_id);old=snap(item);item.status="Blocked";item.updated_by_user_id=user.id;audit(db,user,AuditAction.VISITOR_BLOCKED,AuditModule.VISITORS,item,old);db.commit();return visitor_visible(item,user)
@router.post("/visitors/{visitor_id}/activate")
def activate(visitor_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.block"))):
    item=visitor_or_404(db,visitor_id);old=snap(item);item.status="Active" if item.is_verified else "Pending Verification";item.updated_by_user_id=user.id;audit(db,user,AuditAction.VISITOR_ACTIVATED,AuditModule.VISITORS,item,old);db.commit();return visitor_visible(item,user)

def visit_response(db,item):return visit_rows(db,base_visit_query().where(ChildVisit.id==item.id))[0]
@router.get("/child-visits")
def list_visits(date_filter:date|None=Query(None,alias="date"),child_id:int|None=None,visitor_id:int|None=None,approval_status:str|None=None,visit_status:str|None=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):
    stmt=base_visit_query()
    for value,column in ((date_filter,ChildVisit.visit_date),(child_id,ChildVisit.child_id),(visitor_id,ChildVisit.visitor_id),(approval_status,ChildVisit.approval_status),(visit_status,ChildVisit.visit_status)):
        if value is not None:stmt=stmt.where(column==value)
    return visit_rows(db,stmt.order_by(ChildVisit.visit_date.desc(),ChildVisit.visit_code).offset(offset).limit(limit))
@router.post("/child-visits",status_code=201)
def create_visit(payload:ChildVisitCreate,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.create"))):
    if db.get(Child,payload.child_id) is None:raise HTTPException(404,"Child not found")
    visitor=visitor_or_404(db,payload.visitor_id)
    if visitor.status=="Blocked":raise HTTPException(409,"Blocked visitors cannot be scheduled")
    values=payload.model_dump();values["relationship_to_child"]=values["relationship_to_child"] or visitor.relationship_to_child;item=ChildVisit(**values,created_by_user_id=user.id,updated_by_user_id=user.id);db.add(item)
    try:db.flush();audit(db,user,AuditAction.CHILD_VISIT_CREATED,AuditModule.CHILD_VISITS,item);db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,"Visit code already exists")
    return visit_response(db,item)
@router.get("/child-visits/{visit_id}")
def get_visit(visit_id:int,db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):return visit_response(db,visit_or_404(db,visit_id))
@router.put("/child-visits/{visit_id}")
def update_visit(visit_id:int,payload:ChildVisitUpdate,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.update"))):
    item=visit_or_404(db,visit_id)
    if item.visit_status=="Completed" and not roles(user)&{"Admin","Manager"}:raise HTTPException(409,"Completed visits may only be edited by Admin or Manager")
    old=snap(item)
    for key,value in payload.model_dump(exclude_unset=True).items():setattr(item,key,value)
    item.updated_by_user_id=user.id;item.updated_at=datetime.now(UTC);audit(db,user,AuditAction.CHILD_VISIT_UPDATED,AuditModule.CHILD_VISITS,item,old);db.commit();return visit_response(db,item)
@router.delete("/child-visits/{visit_id}")
def delete_visit(visit_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.delete"))):return cancel_visit(visit_id,db,user)
@router.post("/child-visits/{visit_id}/approve")
def approve_visit(visit_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.approve"))):
    item=visit_or_404(db,visit_id);visitor=visitor_or_404(db,item.visitor_id)
    if not visitor.is_verified and "Admin" not in roles(user):raise HTTPException(409,"Visitor must be verified before approval")
    if visitor.status=="Blocked":raise HTTPException(409,"Blocked visitors cannot be approved")
    old=snap(item);item.approval_status="Approved";item.approved_by_user_id=user.id;item.updated_by_user_id=user.id;audit(db,user,AuditAction.CHILD_VISIT_APPROVED,AuditModule.CHILD_VISITS,item,old);db.commit();return visit_response(db,item)
@router.post("/child-visits/{visit_id}/reject")
def reject_visit(visit_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.reject"))):
    item=visit_or_404(db,visit_id);old=snap(item);item.approval_status="Rejected";item.updated_by_user_id=user.id;audit(db,user,AuditAction.CHILD_VISIT_REJECTED,AuditModule.CHILD_VISITS,item,old);db.commit();return visit_response(db,item)
@router.post("/child-visits/{visit_id}/check-in")
def check_in(visit_id:int,payload:VisitCheckInRequest,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.check_in"))):
    item=visit_or_404(db,visit_id)
    if item.approval_status!="Approved":raise HTTPException(409,"Only approved visits can check in")
    if visitor_or_404(db,item.visitor_id).status=="Blocked":raise HTTPException(409,"Blocked visitor cannot check in")
    if item.visit_status!="Scheduled":raise HTTPException(409,"Visit is not awaiting check-in")
    old=snap(item);item.check_in_time=payload.check_in_time or datetime.now().time().replace(microsecond=0);item.supervised_by_user_id=payload.supervised_by_user_id or item.supervised_by_user_id or user.id;item.visit_status="Checked In";item.updated_by_user_id=user.id;audit(db,user,AuditAction.CHILD_VISIT_CHECKED_IN,AuditModule.CHILD_VISITS,item,old);db.commit();return visit_response(db,item)
@router.post("/child-visits/{visit_id}/check-out")
def check_out(visit_id:int,payload:VisitCheckOutRequest,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.check_out"))):
    item=visit_or_404(db,visit_id)
    if item.visit_status!="Checked In" or not item.check_in_time:raise HTTPException(409,"Visit is not checked in")
    check_out_value=payload.check_out_time or datetime.now().time().replace(microsecond=0)
    if check_out_value<item.check_in_time:raise HTTPException(422,"Check-out time cannot be before check-in time")
    old=snap(item);item.check_out_time=check_out_value;item.visit_status="Completed";item.updated_by_user_id=user.id;audit(db,user,AuditAction.CHILD_VISIT_CHECKED_OUT,AuditModule.CHILD_VISITS,item,old);db.commit();return visit_response(db,item)
@router.post("/child-visits/{visit_id}/cancel")
def cancel_visit(visit_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.cancel"))):
    item=visit_or_404(db,visit_id)
    if item.visit_status=="Completed":raise HTTPException(409,"Completed visits cannot be cancelled")
    old=snap(item);item.visit_status="Cancelled";item.approval_status="Cancelled";item.updated_by_user_id=user.id;audit(db,user,AuditAction.CHILD_VISIT_CANCELLED,AuditModule.CHILD_VISITS,item,old);db.commit();return visit_response(db,item)

@router.get("/children/{child_id}/visits")
def child_visits(child_id:int,db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):return visit_rows(db,base_visit_query().where(ChildVisit.child_id==child_id).order_by(ChildVisit.visit_date.desc()))
@router.get("/children/{child_id}/visitors")
def child_visitors(child_id:int,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.view"))):
    items=db.scalars(select(Visitor).join(ChildVisit,ChildVisit.visitor_id==Visitor.id).where(ChildVisit.child_id==child_id,Visitor.deleted_at.is_(None)).distinct()).all();return [visitor_visible(item,user) for item in items]
@router.get("/reports/visitors")
def visitors_report(db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.view"))):return [visitor_visible(item,user) for item in db.scalars(select(Visitor).where(Visitor.deleted_at.is_(None)).order_by(Visitor.full_name)).all()]
@router.get("/reports/child-visits")
def visits_report(db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):return report_projection(visit_rows(db,base_visit_query().order_by(ChildVisit.visit_date.desc())))
@router.get("/reports/daily-visitor-register")
def daily_report(report_date:date=Query(default_factory=date.today,alias="date"),db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):return report_projection(daily_rows(db,report_date))
@router.get("/reports/monthly-visitor-register")
def monthly_report(month:int=Query(...,ge=1,le=12),year:int=Query(...,ge=2000,le=2100),db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):return report_projection(monthly_rows(db,month,year))
@router.get("/dashboard/visitors",response_model=VisitorDashboardResponse)
def visitor_dashboard(db:Session=Depends(get_db),_:User=Depends(require_permission("child_visits.view"))):
    today=date.today();count=lambda model,*filters:db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    return {"today_scheduled":count(ChildVisit,ChildVisit.visit_date==today,ChildVisit.visit_status=="Scheduled"),"pending_approvals":count(ChildVisit,ChildVisit.approval_status=="Pending"),"checked_in":count(ChildVisit,ChildVisit.visit_status=="Checked In"),"completed_today":count(ChildVisit,ChildVisit.visit_date==today,ChildVisit.visit_status=="Completed"),"blocked_visitors":count(Visitor,Visitor.deleted_at.is_(None),Visitor.status=="Blocked"),"pending_verification":count(Visitor,Visitor.deleted_at.is_(None),Visitor.is_verified.is_(False))}

def export_response(db,user,title,filename,rows,kind,permission):
    if not has_permission(user,permission):raise HTTPException(403,f"Permission required: {permission}")
    stream=build_pdf_report(title,rows,user.username,{},report_branding(db)) if kind=="pdf" else build_excel_report(title,rows,user.username,{})
    add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_PDF if kind=="pdf" else AuditAction.EXPORT_EXCEL,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":filename});db.commit();media="application/pdf" if kind=="pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";return StreamingResponse(stream,media_type=media,headers={"Content-Disposition":f'attachment; filename="{filename}.{kind}"'})
@router.get("/exports/visitors.{kind}")
def export_visitors(kind:str,db:Session=Depends(get_db),user:User=Depends(require_permission("visitors.export"))):
    if kind not in {"pdf","xlsx"}:raise HTTPException(404)
    rows=[{"visitor_code":v.visitor_code,"full_name":v.full_name,"relationship":v.relationship_to_child,"district":v.district,"province":v.province,"verified":v.is_verified,"status":v.status} for v in db.scalars(select(Visitor).where(Visitor.deleted_at.is_(None))).all()];return export_response(db,user,"Visitor List","ccms-visitors",rows,kind,"visitors.export")
@router.get("/exports/child-visits.{kind}")
def export_visits(kind:str,db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.export"))):
    if kind not in {"pdf","xlsx"}:raise HTTPException(404)
    return export_response(db,user,"Child Visit Register","ccms-child-visits",report_projection(visit_rows(db,base_visit_query().order_by(ChildVisit.visit_date.desc()))),kind,"child_visits.export")
@router.get("/exports/daily-visitor-register.{kind}")
def export_daily(kind:str,report_date:date=Query(default_factory=date.today,alias="date"),db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.export"))):
    if kind not in {"pdf","xlsx"}:raise HTTPException(404)
    return export_response(db,user,"Daily Visitor Meeting Register",f"ccms-daily-visitor-{report_date}",report_projection(daily_rows(db,report_date)),kind,"child_visits.export")
@router.get("/exports/monthly-visitor-register.{kind}")
def export_monthly(kind:str,month:int=Query(...,ge=1,le=12),year:int=Query(...,ge=2000,le=2100),db:Session=Depends(get_db),user:User=Depends(require_permission("child_visits.export"))):
    if kind not in {"pdf","xlsx"}:raise HTTPException(404)
    return export_response(db,user,"Monthly Visitor Meeting Summary",f"ccms-monthly-visitors-{year}-{month:02d}",report_projection(monthly_rows(db,month,year)),kind,"child_visits.export")
