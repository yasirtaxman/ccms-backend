from datetime import date
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.child import Child
from app.models.child_attendance import DailyChildAttendance

def attendance_or_404(db:Session,attendance_id:int):
    record=db.scalar(select(DailyChildAttendance).where(DailyChildAttendance.id==attendance_id,DailyChildAttendance.deleted_at.is_(None)))
    if record is None: raise HTTPException(404,"Daily attendance record not found")
    return record

def child_or_404(db:Session,child_id:int):
    child=db.get(Child,child_id)
    if child is None: raise HTTPException(404,"Child not found")
    return child

def snapshot(record):
    return {"child_id":record.child_id,"attendance_date":record.attendance_date,"status":record.status,"check_in_time":record.check_in_time,"check_out_time":record.check_out_time,"remarks":record.remarks}

def status_counts(db:Session,target:date):
    rows=db.execute(select(DailyChildAttendance.status,func.count()).join(Child,Child.id==DailyChildAttendance.child_id).where(DailyChildAttendance.attendance_date==target,DailyChildAttendance.deleted_at.is_(None),Child.status=="Active").group_by(DailyChildAttendance.status)).all()
    return dict(rows)

def today_summary(db:Session,target:date=date.today()):
    counts=status_counts(db,target); total=db.scalar(select(func.count()).select_from(Child).where(Child.status=="Active")) or 0; marked=sum(counts.values())
    return {"today_total_children":total,"today_present":counts.get("Present",0),"today_absent":counts.get("Absent",0),"today_on_leave":counts.get("On Leave",0),"today_medical_leave":counts.get("Medical Leave",0),"today_home_visit":counts.get("Home Visit",0),"today_unauthorized_absence":counts.get("Unauthorized Absence",0),"today_missing":counts.get("Missing",0),"attendance_marked_today":marked,"attendance_pending_today":max(total-marked,0)}
