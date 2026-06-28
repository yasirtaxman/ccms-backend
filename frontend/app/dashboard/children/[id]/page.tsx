"use client";

import Link from "next/link";
import { use, useEffect, useMemo, useState } from "react";
import { ChildProfileHeader } from "@/components/children/ChildProfileHeader";
import { ChildProfileSummary } from "@/components/children/ChildProfileSummary";
import { ChildDocumentsPanel } from "@/components/children/ChildDocumentsPanel";
import { AttendanceStatusBadge } from "@/components/children/AttendanceStatusBadge";
import { ChildDevelopmentSummary } from "@/components/development/ChildDevelopmentSummary";
import { childrenApi } from "@/lib/children";
import { visitorsApi } from "@/lib/visitors";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { Child, ChildCompleteProfile } from "@/types/children";
import type { DailyAttendance } from "@/types/attendance";
import type { ChildVisit } from "@/types/visitors";

export default function ChildProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const childId = Number(id);
  const { hasAnyRole, isViewer, hasPermission } = usePermissions();
  const canEdit = hasAnyRole(["Admin", "Manager", "Data Entry Operator"]);
  const [child, setChild] = useState<Child | null>(null);
  const [summary, setSummary] = useState<ChildCompleteProfile | null>(null);
  const [attendance, setAttendance] = useState<DailyAttendance[]>([]);
  const [visits, setVisits] = useState<ChildVisit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      childrenApi.get(childId),
      childrenApi.summary(childId),
      childrenApi.childAttendance(childId),
      visitorsApi.childVisits(childId),
    ]).then(([c, s, a, v]) => {
      setChild(c);
      setSummary(s);
      setAttendance(a);
      setVisits(v);
    }).catch((e) => setError(apiErrorMessage(e))).finally(() => setLoading(false));
  }, [childId]);

  const stats = useMemo(() => ({
    present: attendance.filter((x) => x.status === "Present").length,
    absent: attendance.filter((x) => x.status === "Absent").length,
    leave: attendance.filter((x) => x.status.includes("Leave") || x.status === "Home Visit").length,
  }), [attendance]);

  if (loading) return <div className="panel">Loading child profile…</div>;
  if (error || !child) return <div className="notice-error">{error || "Child record not found."}</div>;

  const viewer = isViewer();
  return (
    <div className="space-y-7">
      <ChildProfileHeader child={child} canEdit={canEdit} />
      <div className="grid gap-5 lg:grid-cols-2">
        <Info title="Basic information" values={{ "Child ID": child.child_id, "Admission file": child.admission_file_no, "Full name": child.full_name, "Father name": child.father_name, "Gender": child.gender, "Date of birth": child.date_of_birth, "Status": child.status }} />
        {hasPermission("children.documents.view") && <Info title="Guardian information" values={{ "Guardian name": child.guardian_name, "Relationship": child.guardian_relationship, ...(!viewer ? { "CNIC / passport": child.guardian_cnic, "Mobile": child.guardian_mobile } : {}) }} />}
        <Info title="Location" values={{ "District": child.district, "Province": child.province }} />
        <Info title="Admission information" values={{ "Admission date": child.admission_date, "Reason for admission": child.reason_for_admission }} />
      </div>

      {summary && <ChildProfileSummary summary={summary} sectionKeys={["admission_documents", "sponsorship", "accommodation", "medical", "education", "case_management"]} />}
      {hasPermission("development.view") && <ChildDevelopmentSummary childId={childId} />}
      {summary && <ChildProfileSummary summary={summary} sectionKeys={["daily_attendance"]} showHeading={false} />}

      <section className="panel">
        <div className="panel-title">
          <div><h2>Daily attendance summary</h2><p className="mt-1 text-sm text-slate-500">Recent presence records for this child</p></div>
          {attendance[0] && <AttendanceStatusBadge status={attendance[0].status} />}
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Records" value={attendance.length} />
          <Stat label="Present" value={stats.present} />
          <Stat label="Absent" value={stats.absent} />
          <Stat label="Leave / visit" value={stats.leave} />
        </div>
      </section>

      <section className="panel">
        <div className="panel-title">
          <div><h2>Visitor / Meeting History</h2><p className="mt-1 text-sm text-slate-500">Recent supervised child meetings</p></div>
          <Link href={`/dashboard/child-visits?child_id=${childId}`} className="secondary-button">Full visit history</Link>
        </div>
        {visits.length ? <div className="table-shell"><table className="data-table"><thead><tr><th>Date</th><th>Visitor</th><th>Relationship</th><th>Purpose</th><th>Supervisor</th><th>Status</th></tr></thead><tbody>{visits.slice(0, 5).map((visit) => <tr key={visit.id}><td>{visit.visit_date}</td><td>{visit.visitor_name}</td><td>{visit.relationship_to_child}</td><td>{visit.meeting_purpose}</td><td>{visit.supervisor_name || "Not assigned"}</td><td>{visit.visit_status}</td></tr>)}</tbody></table></div> : <div className="empty-inline">No visitor meetings recorded.</div>}
      </section>

      {hasPermission("children.documents.view") && <ChildDocumentsPanel childId={childId} />}
    </div>
  );
}

function Info({ title, values }: { title: string; values: Record<string, string | undefined> }) {
  return <section className="panel"><h2 className="mb-4 text-lg font-bold">{title}</h2><dl className="grid gap-3 sm:grid-cols-2">{Object.entries(values).map(([label, value]) => <div key={label}><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</dt><dd className="mt-1 text-sm font-medium text-slate-800">{value || "Not recorded"}</dd></div>)}</dl></section>;
}

function Stat({ label, value }: { label: string; value: number }) {
  return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block text-xl">{value}</strong></div>;
}
