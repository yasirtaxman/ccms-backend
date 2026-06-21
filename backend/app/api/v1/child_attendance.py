from calendar import monthrange
from datetime import UTC, date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.deps import can_create_or_update, can_operational_read, get_db, require_admin
from app.models.child import Child
from app.models.child_attendance import DailyChildAttendance
from app.models.user import User
from app.schemas.child_attendance import (BulkAttendanceRequest,BulkAttendanceResponse,DashboardAttendanceResponse,DailyAttendanceCreate,DailyAttendanceResponse,DailyAttendanceUpdate,MonthlyAttendanceRow,PaginatedAttendanceResponse,TodayAttendanceChild,TodayAttendanceResponse)
from app.services.audit import AuditAction,AuditModule,add_audit_log
from app.services.child_attendance_service import attendance_or_404,child_or_404,snapshot,today_summary

router=APIRouter(tags=["Daily Child Attendance"])

def query_records(from_date=None,to_date=None,attendance_status=None,child_id=None,district=None,gender=None):
    stmt=select(DailyChildAttendance,Child).join(Child,Child.id==DailyChildAttendance.child_id).where(DailyChildAttendance.deleted_at.is_(None))
    if from_date: stmt=stmt.where(DailyChildAttendance.attendance_date>=from_date)
    if to_date: stmt=stmt.where(DailyChildAttendance.attendance_date<=to_date)
    if attendance_status: stmt=stmt.where(DailyChildAttendance.status==attendance_status)
    if child_id: stmt=stmt.where(DailyChildAttendance.child_id==child_id)
    if district: stmt=stmt.where(Child.district.ilike(f"%{district}%"))
    if gender: stmt=stmt.where(Child.gender==gender)
    return stmt

def response(record,child):
    values={column:getattr(record,column) for column in ("id","child_id","attendance_date","status","check_in_time","check_out_time","remarks","marked_by","created_by","updated_by","created_at","updated_at")}
    values.update(child_code=child.child_id,child_name=child.full_name,gender=child.gender,district=child.district)
    return values

@router.post("/children/{child_id}/daily-attendance",response_model=DailyAttendanceResponse,status_code=status.HTTP_201_CREATED)
def create(child_id:int,payload:DailyAttendanceCreate,db:Session=Depends(get_db),user:User=Depends(can_create_or_update)):
    child_or_404(db,child_id)
    existing=db.scalar(select(DailyChildAttendance).where(DailyChildAttendance.child_id==child_id,DailyChildAttendance.attendance_date==payload.attendance_date,DailyChildAttendance.deleted_at.is_(None)))
    if existing: raise HTTPException(409,"Attendance already exists for this child and date")
    record=DailyChildAttendance(child_id=child_id,marked_by=user.id,created_by=user.id,updated_by=user.id,**payload.model_dump());db.add(record)
    try:
        db.flush();add_audit_log(db,user_id=user.id,action=AuditAction.DAILY_ATTENDANCE_CREATE,module=AuditModule.DAILY_ATTENDANCE,record_id=record.id,new_values=snapshot(record));db.commit()
    except IntegrityError: db.rollback();raise HTTPException(409,"Attendance already exists for this child and date")
    return record

@router.get("/children/{child_id}/daily-attendance",response_model=list[DailyAttendanceResponse])
def child_history(child_id:int,from_date:date|None=None,to_date:date|None=None,status_filter:str|None=Query(None,alias="status"),db:Session=Depends(get_db),_:User=Depends(can_operational_read)):
    child_or_404(db,child_id);stmt=query_records(from_date,to_date,status_filter,child_id)
    return [record for record,_child in db.execute(stmt.order_by(DailyChildAttendance.attendance_date.desc())).all()]

@router.get("/daily-attendance",response_model=PaginatedAttendanceResponse)
def list_attendance(date_filter:date|None=Query(None,alias="date"),from_date:date|None=None,to_date:date|None=None,status_filter:str|None=Query(None,alias="status"),child_id:int|None=None,limit:int=Query(50,ge=1,le=500),offset:int=Query(0,ge=0),db:Session=Depends(get_db),_:User=Depends(can_operational_read)):
    if date_filter: from_date=to_date=date_filter
    stmt=query_records(from_date,to_date,status_filter,child_id);total=db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows=db.execute(stmt.order_by(DailyChildAttendance.attendance_date.desc(),Child.full_name).offset(offset).limit(limit)).all()
    return {"data":[response(r,c) for r,c in rows],"total":total,"limit":limit,"offset":offset}

@router.put("/daily-attendance/{attendance_id}",response_model=DailyAttendanceResponse)
def update(attendance_id:int,payload:DailyAttendanceUpdate,db:Session=Depends(get_db),user:User=Depends(can_create_or_update)):
    record=attendance_or_404(db,attendance_id);old=snapshot(record)
    for key,value in payload.model_dump(exclude_unset=True).items(): setattr(record,key,value)
    record.marked_by=user.id;record.updated_by=user.id;record.updated_at=datetime.now(UTC)
    add_audit_log(db,user_id=user.id,action=AuditAction.DAILY_ATTENDANCE_UPDATE,module=AuditModule.DAILY_ATTENDANCE,record_id=record.id,old_values=old,new_values=snapshot(record))
    try: db.commit()
    except IntegrityError: db.rollback();raise HTTPException(409,"Attendance already exists for this child and date")
    return record

@router.delete("/daily-attendance/{attendance_id}")
def delete(attendance_id:int,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    record=attendance_or_404(db,attendance_id);old=snapshot(record);record.deleted_at=datetime.now(UTC);record.deleted_by=user.id;record.updated_by=user.id
    add_audit_log(db,user_id=user.id,action=AuditAction.DAILY_ATTENDANCE_DELETE,module=AuditModule.DAILY_ATTENDANCE,record_id=record.id,old_values=old,new_values={"deleted":True});db.commit();return {"message":"Daily attendance deleted successfully","attendance_id":record.id}

@router.post("/daily-attendance/bulk-mark",response_model=BulkAttendanceResponse)
def bulk_mark(payload:BulkAttendanceRequest,db:Session=Depends(get_db),user:User=Depends(can_create_or_update)):
    ids=[item.child_id for item in payload.records]
    if len(ids)!=len(set(ids)): raise HTTPException(422,"Each child may appear only once in a bulk attendance request")
    existing_children=set(db.scalars(select(Child.id).where(Child.id.in_(ids))).all())
    missing=sorted(set(ids)-existing_children)
    if missing: raise HTTPException(422,f"Unknown child IDs: {missing}")
    existing={r.child_id:r for r in db.scalars(select(DailyChildAttendance).where(DailyChildAttendance.child_id.in_(ids),DailyChildAttendance.attendance_date==payload.attendance_date,DailyChildAttendance.deleted_at.is_(None))).all()}
    created=updated=0
    for item in payload.records:
        values=item.model_dump(exclude={"child_id"});record=existing.get(item.child_id)
        if record:
            for key,value in values.items(): setattr(record,key,value)
            record.marked_by=user.id;record.updated_by=user.id;record.updated_at=datetime.now(UTC);updated+=1
        else:
            db.add(DailyChildAttendance(child_id=item.child_id,attendance_date=payload.attendance_date,marked_by=user.id,created_by=user.id,updated_by=user.id,**values));created+=1
    add_audit_log(db,user_id=user.id,action=AuditAction.DAILY_ATTENDANCE_BULK_MARK,module=AuditModule.DAILY_ATTENDANCE,new_values={"attendance_date":payload.attendance_date,"created_count":created,"updated_count":updated,"child_ids":ids});db.commit()
    return {"created_count":created,"updated_count":updated,"errors":[]}

@router.get("/daily-attendance/today",response_model=TodayAttendanceResponse)
def today(db:Session=Depends(get_db),_:User=Depends(can_operational_read)):
    target=date.today();summary=today_summary(db,target)
    rows=db.execute(select(Child,DailyChildAttendance).outerjoin(DailyChildAttendance,and_(DailyChildAttendance.child_id==Child.id,DailyChildAttendance.attendance_date==target,DailyChildAttendance.deleted_at.is_(None))).where(Child.status=="Active").order_by(Child.full_name)).all()
    records=[TodayAttendanceChild(child_id=c.id,child_code=c.child_id,full_name=c.full_name,gender=c.gender,district=c.district,attendance_id=a.id if a else None,status=a.status if a else None,check_in_time=a.check_in_time if a else None,check_out_time=a.check_out_time if a else None,remarks=a.remarks if a else None) for c,a in rows]
    return {"attendance_date":target,"records":records,**summary}

@router.get("/reports/daily-attendance",response_model=list[dict])
def daily_report(from_date:date|None=None,to_date:date|None=None,status_filter:str|None=Query(None,alias="status"),child_id:int|None=None,district:str|None=None,gender:str|None=None,db:Session=Depends(get_db),_:User=Depends(can_operational_read)):
    rows=db.execute(query_records(from_date,to_date,status_filter,child_id,district,gender).order_by(DailyChildAttendance.attendance_date.desc(),Child.full_name).limit(5000)).all();return [response(r,c) for r,c in rows]

@router.get("/reports/monthly-child-attendance",response_model=list[MonthlyAttendanceRow])
def monthly_report(month:int=Query(...,ge=1,le=12),year:int=Query(...,ge=2000,le=2100),child_id:int|None=None,db:Session=Depends(get_db),_:User=Depends(can_operational_read)):
    start=date(year,month,1);end=date(year,month,monthrange(year,month)[1]);status_col=DailyChildAttendance.status
    stmt=select(Child.id,Child.child_id,Child.full_name,func.sum(case((status_col=="Present",1),else_=0)),func.sum(case((status_col=="Absent",1),else_=0)),func.sum(case((status_col=="On Leave",1),else_=0)),func.sum(case((status_col=="Medical Leave",1),else_=0)),func.sum(case((status_col=="Home Visit",1),else_=0)),func.sum(case((status_col=="Unauthorized Absence",1),else_=0)),func.sum(case((status_col=="Missing",1),else_=0)),func.count(DailyChildAttendance.id)).join(DailyChildAttendance,DailyChildAttendance.child_id==Child.id).where(DailyChildAttendance.attendance_date.between(start,end),DailyChildAttendance.deleted_at.is_(None)).group_by(Child.id,Child.child_id,Child.full_name)
    if child_id: stmt=stmt.where(Child.id==child_id)
    result=[]
    for row in db.execute(stmt.order_by(Child.full_name)):
        present,absent,leave,medical,home,unauthorized,missing,total=[int(v or 0) for v in row[3:]];result.append({"child_id":row[0],"child_code":row[1],"child_name":row[2],"present_days":present,"absent_days":absent,"leave_days":leave,"medical_leave_days":medical,"home_visit_days":home,"unauthorized_absence_days":unauthorized,"missing_days":missing,"attendance_percentage":round(present*100/total,2) if total else 0})
    return result

@router.get("/dashboard/daily-attendance",response_model=DashboardAttendanceResponse)
def attendance_dashboard(db:Session=Depends(get_db),_:User=Depends(can_operational_read)): return today_summary(db)
