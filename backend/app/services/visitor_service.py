from datetime import UTC,date,datetime,time
from fastapi import HTTPException
from sqlalchemy import func,or_,select
from sqlalchemy.orm import Session
from app.models.child import Child
from app.models.user import User
from app.models.visitor import ChildVisit,Visitor

def visitor_or_404(db,id,include_deleted=False):
    visitor=db.get(Visitor,id)
    if visitor is None or (visitor.deleted_at is not None and not include_deleted):raise HTTPException(404,"Visitor not found")
    return visitor
def visit_or_404(db,id):
    item=db.get(ChildVisit,id)
    if item is None:raise HTTPException(404,"Child visit not found")
    return item
def roles(user):return {role.name for role in user.roles}
def can_sensitive(user):return bool(roles(user)&{"Admin","Manager"})
def visitor_visible(visitor,user):
    if can_sensitive(user):return {column.name:getattr(visitor,column.name) for column in Visitor.__table__.columns if column.name not in {"deleted_at","deleted_by_user_id"}}
    return {key:getattr(visitor,key) for key in ("id","visitor_code","full_name","relationship_to_child","district","province","photo_path","is_verified","status","created_at","updated_at")}
def visit_rows(db,stmt):
    rows=db.execute(stmt.join(Child,Child.id==ChildVisit.child_id).join(Visitor,Visitor.id==ChildVisit.visitor_id).outerjoin(User,User.id==ChildVisit.supervised_by_user_id)).all()
    return [{**{column.name:getattr(visit,column.name) for column in ChildVisit.__table__.columns},"child_code":child.child_id,"child_name":child.full_name,"visitor_name":visitor.full_name,"supervisor_name":supervisor.full_name if supervisor else None} for visit,child,visitor,supervisor in rows]
def base_visit_query():return select(ChildVisit,Child,Visitor,User)
def daily_rows(db,target):return visit_rows(db,base_visit_query().where(ChildVisit.visit_date==target).order_by(ChildVisit.check_in_time,ChildVisit.visit_code))
def monthly_rows(db,month,year):
    start=date(year,month,1);end=(date(year+1,1,1) if month==12 else date(year,month+1,1));return visit_rows(db,base_visit_query().where(ChildVisit.visit_date>=start,ChildVisit.visit_date<end).order_by(ChildVisit.visit_date,ChildVisit.visit_code))
def report_projection(rows):
    keys=("visit_code","visit_date","child_code","child_name","visitor_name","relationship_to_child","meeting_purpose","meeting_location","supervisor_name","approval_status","visit_status","check_in_time","check_out_time","remarks")
    return [{key:row.get(key) for key in keys} for row in rows]
