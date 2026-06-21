import Link from "next/link";
import { Eye, FileText, Pencil } from "lucide-react";
import type { Child } from "@/types/children";
import { ageFromDate } from "@/lib/children";

export function ChildrenTable({rows,canEdit}:{rows:Child[];canEdit:boolean}) {
  if (!rows.length) return <div className="empty-card"><h2>No children found</h2><p>Adjust the filters or add the first child record.</p></div>;
  return <div className="table-shell"><table className="data-table"><thead><tr><th>Child</th><th>Admission File</th><th>Father</th><th>Gender / Age</th><th>District</th><th>Admission</th><th>Status</th><th>Actions</th></tr></thead><tbody>{rows.map(child=><tr key={child.id}><td><strong>{child.full_name}</strong><span>{child.child_id}</span></td><td>{child.admission_file_no}</td><td>{child.father_name||"—"}</td><td>{child.gender} · {ageFromDate(child.date_of_birth)}</td><td>{child.district}</td><td>{child.admission_date}</td><td><span className={`status-pill status-${child.status.toLowerCase()}`}>{child.status}</span></td><td><div className="flex gap-1"><Link title="View" className="icon-button" href={`/dashboard/children/${child.id}`}><Eye size={16}/></Link>{canEdit&&<Link title="Edit" className="icon-button" href={`/dashboard/children/${child.id}/edit`}><Pencil size={16}/></Link>}<Link title="Complete profile and documents" className="icon-button" href={`/dashboard/children/${child.id}#summary`}><FileText size={16}/></Link></div></td></tr>)}</tbody></table></div>;
}
