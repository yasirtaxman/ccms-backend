"use client";
import { useSearchParams } from "next/navigation";import { DailyAttendanceRegister } from "@/components/children/DailyAttendanceRegister";
export default function AttendancePage(){const search=useSearchParams();const child=search.get("child");return <div className="space-y-6"><div><p className="eyebrow">Daily presence register</p><h1 className="page-title">Daily child attendance</h1><p className="page-subtitle">Track orphanage, shelter, and hostel presence separately from academic attendance.</p></div><DailyAttendanceRegister initialChild={child?Number(child):undefined}/></div>}
