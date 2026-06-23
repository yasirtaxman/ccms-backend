from datetime import date, timedelta
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.accommodation import Bed,BedAllocation,Block,Building,Floor,Room
from app.models.attendance import Attendance
from app.models.case_management import CarePlan,CaseNote,ChildCaseProfile,IncidentRecord
from app.models.child import Child
from app.models.child_attendance import DailyChildAttendance
from app.models.document import Document
from app.models.education_record import EducationRecord
from app.models.exam_result import ExamResult
from app.models.medical_profile import MedicalProfile
from app.models.medication import Medication
from app.models.school import School
from app.models.sponsor import ChildSponsorship,Sponsor
from app.models.vaccination import Vaccination
from app.models.visitor import ChildVisit,Visitor

REQUIRED_DOCUMENTS={"Admission Form","Child Photo","Birth Certificate / Form-B","Guardian CNIC","Father Death Certificate","Medical Certificate"}

def _age(born:date,today:date)->int:return today.year-born.year-((today.month,today.day)<(born.month,born.day))
def _mask(value:str|None,visible:int=4)->str:
    if not value:return "Not recorded"
    compact=value.strip();return "*"*max(len(compact)-visible,4)+compact[-visible:]
def _yes(value)->str:return "Yes" if value else "No"
def _fields(**values):return [(key.replace("_"," ").title(),value) for key,value in values.items()]

def build_full_child_profile(db:Session,child_id:int,roles:set[str])->dict:
    child=db.get(Child,child_id)
    if child is None:
        from fastapi import HTTPException
        raise HTTPException(404,"Child not found")
    today=date.today();admin="Admin" in roles;viewer="Viewer" in roles and not admin
    documents=list(db.scalars(select(Document).where(Document.child_id==child_id).order_by(Document.document_type)).all())
    verified=sum(1 for item in documents if item.is_verified)
    sponsorships=db.execute(select(ChildSponsorship,Sponsor).join(Sponsor,Sponsor.id==ChildSponsorship.sponsor_id).where(ChildSponsorship.child_id==child_id,ChildSponsorship.status=="Active",ChildSponsorship.start_date<=today,or_(ChildSponsorship.end_date.is_(None),ChildSponsorship.end_date>=today),Sponsor.deleted_at.is_(None)).order_by(ChildSponsorship.start_date.desc())).all()
    bed=db.execute(select(BedAllocation,Bed,Room,Floor,Block,Building).join(Bed,Bed.id==BedAllocation.bed_id).join(Room,Room.id==Bed.room_id).join(Floor,Floor.id==Room.floor_id).join(Block,Block.id==Floor.block_id).join(Building,Building.id==Block.building_id).where(BedAllocation.child_id==child_id,BedAllocation.status=="Active")).first()
    medical=db.scalar(select(MedicalProfile).where(MedicalProfile.child_id==child_id))
    education=db.execute(select(EducationRecord,School).join(School,School.id==EducationRecord.school_id).where(EducationRecord.child_id==child_id,EducationRecord.status=="Studying").order_by(EducationRecord.start_date.desc())).first()
    case_profile=db.scalar(select(ChildCaseProfile).where(ChildCaseProfile.child_id==child_id,ChildCaseProfile.deleted_at.is_(None)))
    latest_school_attendance=db.scalar(select(Attendance.attendance_percentage).join(EducationRecord,EducationRecord.id==Attendance.education_record_id).where(EducationRecord.child_id==child_id).order_by(Attendance.year.desc(),Attendance.month.desc()).limit(1))
    latest_exam=db.scalar(select(ExamResult.percentage).join(EducationRecord,EducationRecord.id==ExamResult.education_record_id).where(EducationRecord.child_id==child_id).order_by(ExamResult.exam_date.desc()).limit(1))
    month_start=today.replace(day=1)
    daily_counts=dict(db.execute(select(DailyChildAttendance.status,func.count()).where(DailyChildAttendance.child_id==child_id,DailyChildAttendance.attendance_date.between(month_start,today),DailyChildAttendance.deleted_at.is_(None)).group_by(DailyChildAttendance.status)).all())
    today_status=db.scalar(select(DailyChildAttendance.status).where(DailyChildAttendance.child_id==child_id,DailyChildAttendance.attendance_date==today,DailyChildAttendance.deleted_at.is_(None)))
    visit_counts=dict(db.execute(select(ChildVisit.visit_status,func.count()).where(ChildVisit.child_id==child_id).group_by(ChildVisit.visit_status)).all())
    latest_visits=db.execute(select(ChildVisit,Visitor).join(Visitor,Visitor.id==ChildVisit.visitor_id).where(ChildVisit.child_id==child_id,Visitor.deleted_at.is_(None)).order_by(ChildVisit.visit_date.desc(),ChildVisit.id.desc()).limit(5)).all()
    marked_days=sum(daily_counts.values());present_days=daily_counts.get("Present",0);leave_days=sum(daily_counts.get(status,0) for status in ("On Leave","Medical Leave","Home Visit"))
    guardian_cnic=child.guardian_cnic if admin else _mask(child.guardian_cnic)
    guardian_mobile=_mask(child.guardian_mobile) if viewer else child.guardian_mobile
    sections=[]
    sections.append({"key":"basic","title":"1. Child Basic Information","fields":_fields(full_name=child.full_name,child_id=child.child_id,admission_file_no=child.admission_file_no,gender=child.gender,date_of_birth=child.date_of_birth,age=_age(child.date_of_birth,today),status=child.status,admission_date=child.admission_date,reason_for_admission=child.reason_for_admission)})
    sections.append({"key":"family","title":"2. Parent / Family Information","fields":_fields(father_name=child.father_name,grandfather_name=child.grandfather_name,mother_name=child.mother_name)})
    sections.append({"key":"guardian","title":"3. Guardian Information","fields":_fields(guardian_name=child.guardian_name,guardian_relationship=child.guardian_relationship,guardian_mobile=guardian_mobile,guardian_cnic=guardian_cnic)})
    address_values={"village_mohallah":child.village_mohallah,"union_council":child.union_council,"tehsil":child.tehsil,"district":child.district,"province":child.province}
    if not viewer:address_values={"current_address":child.current_address,"permanent_address":child.permanent_address,**address_values}
    sections.append({"key":"address","title":"4. Address Information","fields":_fields(**address_values),"note":"Full address hidden for Viewer role." if viewer else None})
    sections.append({"key":"documents","title":"5. Admission Documents Summary","fields":_fields(required_documents_count=len(REQUIRED_DOCUMENTS),uploaded_documents_count=len(documents),verified_documents_count=verified,pending_verification_count=len(documents)-verified,admission_documents_complete=_yes(REQUIRED_DOCUMENTS.issubset({d.document_type for d in documents}))),"columns":["Document Type","Uploaded Date","Verified Status","Verified By"],"rows":[[d.document_type,d.uploaded_at,"Verified" if d.is_verified else "Pending","Not recorded"] for d in documents],"empty":"No admission documents have been uploaded."})
    sponsor_rows=[[r.sponsorship_type,(s.full_name if not viewer else "Restricted"),r.start_date,r.end_date or "Open-ended",r.status] for r,s in sponsorships]
    sections.append({"key":"sponsorship","title":"6. Sponsorship Summary","fields":_fields(has_active_sponsor=_yes(bool(sponsorships)),active_sponsor_count=len(sponsorships),sponsorship_type=", ".join(sorted({r.sponsorship_type for r,_ in sponsorships})) or "Not applicable"),"columns":["Type","Sponsor Name","Start Date","End Date","Status"],"rows":sponsor_rows,"empty":"No active sponsorship record found."})
    accommodation_fields=_fields(has_active_bed=_yes(bool(bed)))
    if bed:
        allocation,bed_row,room,floor,block,building=bed;accommodation_fields+=_fields(building=building.building_name,block=block.block_name,floor=floor.floor_name,room=room.room_name,bed=bed_row.bed_name,allocation_date=allocation.allocation_date,bed_status=bed_row.status)
    sections.append({"key":"accommodation","title":"7. Accommodation Summary","fields":accommodation_fields,"empty":"No active accommodation allocation found." if not bed else None})
    medical_fields=_fields(has_medical_profile=_yes(bool(medical)))
    if medical:medical_fields+=_fields(blood_group=medical.blood_group or "Not recorded",active_medication_count=db.scalar(select(func.count()).select_from(Medication).where(Medication.child_id==child_id,Medication.status=="Active")) or 0,upcoming_vaccination_count=db.scalar(select(func.count()).select_from(Vaccination).where(Vaccination.child_id==child_id,Vaccination.next_due_date.between(today,today+timedelta(days=30)))) or 0,special_needs_flag=_yes(bool(medical.special_needs and medical.special_needs.strip())),chronic_disease_flag=_yes(bool(medical.chronic_diseases and medical.chronic_diseases.strip())))
    sections.append({"key":"medical","title":"8. Medical Summary","fields":medical_fields,"empty":"No medical profile found." if not medical else None})
    education_fields=_fields(has_active_education_record=_yes(bool(education)))
    if education:
        record,school=education;education_fields+=_fields(school_name=school.school_name,class_level=record.class_level,academic_year=record.academic_year,latest_attendance_percentage=f"{float(latest_school_attendance):.2f}%" if latest_school_attendance is not None else "Not recorded",latest_exam_percentage=f"{float(latest_exam):.2f}%" if latest_exam is not None else "Not recorded",current_education_status=record.status)
    sections.append({"key":"education","title":"9. Education Summary","fields":education_fields,"empty":"No active education record found." if not education else None})
    case_fields=_fields(has_case_profile=_yes(bool(case_profile)))
    if case_profile:
        case_fields+=_fields(case_status=case_profile.case_status,risk_level=case_profile.risk_level if (admin or "Manager" in roles) else "Restricted",welfare_status=case_profile.welfare_status if (admin or "Manager" in roles) else "Restricted",pending_follow_up_count=db.scalar(select(func.count()).select_from(CaseNote).where(CaseNote.child_id==child_id,CaseNote.deleted_at.is_(None),CaseNote.follow_up_required.is_(True),CaseNote.follow_up_date<=today)) or 0,active_care_plan_count=db.scalar(select(func.count()).select_from(CarePlan).where(CarePlan.child_id==child_id,CarePlan.deleted_at.is_(None),CarePlan.status=="Active")) or 0,critical_incident_count=(db.scalar(select(func.count()).select_from(IncidentRecord).where(IncidentRecord.child_id==child_id,IncidentRecord.deleted_at.is_(None),IncidentRecord.severity=="Critical",IncidentRecord.review_status!="Closed")) or 0) if (admin or "Manager" in roles) else "Restricted")
    sections.append({"key":"case_management","title":"10. Case Management Summary","fields":case_fields,"empty":"No case profile found." if not case_profile else None})
    sections.append({"key":"daily_attendance","title":"11. Daily Attendance Summary","fields":_fields(today_status=today_status or "Not marked",current_month_present_days=present_days,current_month_absent_days=daily_counts.get("Absent",0),current_month_leave_days=leave_days,current_month_attendance_percentage=f"{present_days*100/marked_days:.2f}%" if marked_days else "Not available"),"columns":["Status","Days"],"rows":[[status,count] for status,count in sorted(daily_counts.items())],"empty":"No daily attendance records found for the current month." if not daily_counts else None})
    sections.append({"key":"visitor_history","title":"12. Visitor / Meeting History Summary","fields":_fields(total_visits=sum(visit_counts.values()),completed_visits=visit_counts.get("Completed",0),scheduled_visits=visit_counts.get("Scheduled",0),checked_in_visits=visit_counts.get("Checked In",0),cancelled_visits=visit_counts.get("Cancelled",0)),"columns":["Visit Date","Visitor","Relationship","Purpose","Status"],"rows":[[visit.visit_date,visitor.full_name if not viewer else "Restricted",visitor.relationship_to_child,visit.meeting_purpose,visit.visit_status] for visit,visitor in latest_visits],"empty":"No visitor or child meeting records found." if not latest_visits else None})
    identity={"Child Name":child.full_name,"Child ID":child.child_id,"Admission File No":child.admission_file_no,"Status":child.status,"Gender":child.gender,"Age":_age(child.date_of_birth,today),"Date of Birth":child.date_of_birth,"Admission Date":child.admission_date,"District":child.district,"Province":child.province}
    child_photo=next((document.file_path for document in reversed(documents) if document.document_type=="Child Photo"),None)
    return {"child_id":child.id,"identity":identity,"sections":sections,"child_photo_path":child_photo}
