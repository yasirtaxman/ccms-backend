export const ATTENDANCE_STATUSES=["Present","Absent","On Leave","Medical Leave","Home Visit","School Activity","Outside Activity","Unauthorized Absence","Missing"] as const;
export type AttendanceStatus=typeof ATTENDANCE_STATUSES[number];
export interface DailyAttendance {id:number;child_id:number;attendance_date:string;status:AttendanceStatus;check_in_time:string|null;check_out_time:string|null;remarks:string|null;child_code:string;child_name:string;gender:string;district:string}
export interface AttendancePage {data:DailyAttendance[];total:number;limit:number;offset:number}
export interface AttendanceDraft {child_id:number;status:AttendanceStatus;check_in_time:string;check_out_time:string;remarks:string}
export interface BulkAttendanceResult {created_count:number;updated_count:number;errors:{child_id?:number;message:string}[]}
export interface TodayAttendanceSummary {attendance_date:string;today_total_children:number;today_present:number;today_absent:number;today_on_leave:number;today_medical_leave:number;today_home_visit:number;today_unauthorized_absence:number;today_missing:number;attendance_marked_today:number;attendance_pending_today:number}
export interface MonthlyAttendance {child_id:number;child_code:string;child_name:string;present_days:number;absent_days:number;leave_days:number;medical_leave_days:number;home_visit_days:number;unauthorized_absence_days:number;missing_days:number;attendance_percentage:number}
