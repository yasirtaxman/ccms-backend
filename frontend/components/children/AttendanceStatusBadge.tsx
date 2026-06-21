import type { AttendanceStatus } from "@/types/attendance";
export function AttendanceStatusBadge({status}:{status:AttendanceStatus|null|undefined}){if(!status)return <span className="attendance-badge attendance-pending">Pending</span>;return <span className={`attendance-badge attendance-${status.toLowerCase().replaceAll(" ","-")}`}>{status}</span>}
