from datetime import date, datetime, time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

AttendanceStatus = Literal["Present","Absent","On Leave","Medical Leave","Home Visit","School Activity","Outside Activity","Unauthorized Absence","Missing"]

class AttendanceValues(BaseModel):
    status: AttendanceStatus
    check_in_time: time | None = None
    check_out_time: time | None = None
    remarks: str | None = Field(None, max_length=2000)
    @model_validator(mode="after")
    def validate_times(self):
        if self.check_in_time and self.check_out_time and self.check_out_time < self.check_in_time:
            raise ValueError("check_out_time cannot be earlier than check_in_time")
        return self

class DailyAttendanceCreate(AttendanceValues): attendance_date: date
class DailyAttendanceUpdate(AttendanceValues): attendance_date: date | None = None
class BulkAttendanceRecord(AttendanceValues): child_id: int
class BulkAttendanceRequest(BaseModel): attendance_date: date; records: list[BulkAttendanceRecord] = Field(min_length=1, max_length=5000)

class DailyAttendanceResponse(AttendanceValues):
    id: int; child_id: int; attendance_date: date; marked_by: int; created_by: int; updated_by: int; created_at: datetime; updated_at: datetime
    model_config=ConfigDict(from_attributes=True)

class AttendanceListItem(DailyAttendanceResponse):
    child_code: str; child_name: str; gender: str; district: str

class PaginatedAttendanceResponse(BaseModel): data:list[AttendanceListItem]; total:int; limit:int; offset:int
class BulkAttendanceResponse(BaseModel): created_count:int; updated_count:int; errors:list[dict]
class TodayAttendanceChild(BaseModel): child_id:int; child_code:str; full_name:str; gender:str; district:str; attendance_id:int|None=None; status:AttendanceStatus|None=None; check_in_time:time|None=None; check_out_time:time|None=None; remarks:str|None=None
class TodayAttendanceResponse(BaseModel):
    attendance_date:date; today_total_children:int; today_present:int; today_absent:int; today_on_leave:int; today_medical_leave:int; today_home_visit:int; today_unauthorized_absence:int; today_missing:int; attendance_marked_today:int; attendance_pending_today:int; records:list[TodayAttendanceChild]
class MonthlyAttendanceRow(BaseModel): child_id:int; child_code:str; child_name:str; present_days:int; absent_days:int; leave_days:int; medical_leave_days:int; home_visit_days:int; unauthorized_absence_days:int; missing_days:int; attendance_percentage:float
class DashboardAttendanceResponse(BaseModel):
    today_total_children:int; today_present:int; today_absent:int; today_on_leave:int; today_medical_leave:int; today_home_visit:int; today_unauthorized_absence:int; today_missing:int; attendance_marked_today:int; attendance_pending_today:int
