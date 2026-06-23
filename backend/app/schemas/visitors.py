from datetime import date,datetime,time
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator

VisitorStatus=Literal["Active","Inactive","Blocked","Pending Verification"]
ApprovalStatus=Literal["Pending","Approved","Rejected","Cancelled"]
VisitStatus=Literal["Scheduled","Checked In","Completed","No Show","Cancelled"]
Relationship=Literal["Father","Mother","Brother","Sister","Uncle","Aunt","Grandfather","Grandmother","Guardian","Court Representative","Social Welfare Officer","Other"]
MeetingPurpose=Literal["Family Visit","Guardian Meeting","Case Review","Legal / Court Related","Medical Support","Education Related","Social Welfare Visit","Other"]
MeetingLocation=Literal["Visitor Room","Office","Supervised Hall","Outdoor Area","Other"]

class VisitorCreate(BaseModel):
    visitor_code:str=Field(min_length=2,max_length=50);full_name:str=Field(min_length=2,max_length=255);father_name:str|None=None;cnic_passport:str|None=Field(None,max_length=50);mobile:str|None=Field(None,max_length=30);alternate_mobile:str|None=Field(None,max_length=30);relationship_to_child:Relationship;address:str|None=None;district:str|None=None;province:str|None=None;photo_path:str|None=None;status:VisitorStatus="Pending Verification";remarks:str|None=None
class VisitorUpdate(BaseModel):
    full_name:str|None=Field(None,min_length=2,max_length=255);father_name:str|None=None;cnic_passport:str|None=None;mobile:str|None=None;alternate_mobile:str|None=None;relationship_to_child:Relationship|None=None;address:str|None=None;district:str|None=None;province:str|None=None;photo_path:str|None=None;status:VisitorStatus|None=None;remarks:str|None=None
class VisitorVerifyRequest(BaseModel):verification_method:str=Field(min_length=2,max_length=100)
class VisitorResponse(VisitorCreate):
    id:int;is_verified:bool;verification_method:str|None;verified_by_user_id:int|None;verified_at:datetime|None;created_at:datetime;updated_at:datetime;created_by_user_id:int;updated_by_user_id:int
    model_config=ConfigDict(from_attributes=True)
class VisitorSafeResponse(BaseModel):
    id:int;visitor_code:str;full_name:str;relationship_to_child:str;district:str|None;province:str|None;photo_path:str|None;is_verified:bool;status:VisitorStatus;created_at:datetime;updated_at:datetime
    model_config=ConfigDict(from_attributes=True)

class ChildVisitCreate(BaseModel):
    visit_code:str=Field(min_length=2,max_length=50);child_id:int=Field(gt=0);visitor_id:int=Field(gt=0);relationship_to_child:Relationship|None=None;visit_date:date;meeting_purpose:MeetingPurpose;meeting_location:MeetingLocation;supervised_by_user_id:int|None=Field(None,gt=0);remarks:str|None=None;safety_notes:str|None=None
class ChildVisitUpdate(BaseModel):
    relationship_to_child:Relationship|None=None;visit_date:date|None=None;meeting_purpose:MeetingPurpose|None=None;meeting_location:MeetingLocation|None=None;supervised_by_user_id:int|None=Field(None,gt=0);remarks:str|None=None;safety_notes:str|None=None
class VisitCheckInRequest(BaseModel):check_in_time:time|None=None;supervised_by_user_id:int|None=Field(None,gt=0)
class VisitCheckOutRequest(BaseModel):
    check_out_time:time|None=None
class ChildVisitResponse(BaseModel):
    id:int;visit_code:str;child_id:int;child_code:str|None=None;child_name:str|None=None;visitor_id:int;visitor_name:str|None=None;relationship_to_child:str;visit_date:date;check_in_time:time|None;check_out_time:time|None;meeting_purpose:str;meeting_location:str;supervised_by_user_id:int|None;supervisor_name:str|None=None;approved_by_user_id:int|None;approval_status:ApprovalStatus;visit_status:VisitStatus;remarks:str|None;safety_notes:str|None;created_at:datetime;updated_at:datetime;created_by_user_id:int;updated_by_user_id:int
    model_config=ConfigDict(from_attributes=True)
    @model_validator(mode="after")
    def valid_times(self):
        if self.check_in_time and self.check_out_time and self.check_out_time<self.check_in_time:raise ValueError("check-out cannot precede check-in")
        return self
class VisitorDashboardResponse(BaseModel):today_scheduled:int;pending_approvals:int;checked_in:int;completed_today:int;blocked_visitors:int;pending_verification:int
