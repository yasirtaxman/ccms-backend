"use client";

import { usePermissions } from "@/hooks/usePermissions";
import type { ChildCompleteProfile } from "@/types/children";

const titles: Record<keyof ChildCompleteProfile, string> = {
  child_basic: "Basic summary",
  admission_documents: "Admission documents",
  sponsorship: "Sponsorship",
  accommodation: "Accommodation",
  medical: "Medical",
  education: "Education",
  case_management: "Case management",
  daily_attendance: "Daily attendance",
};

const defaultSectionKeys = (Object.keys(titles) as (keyof ChildCompleteProfile)[]).filter((key) => key !== "child_basic");

export function ChildProfileSummary({
  summary,
  sectionKeys = defaultSectionKeys,
  showHeading = true,
}: {
  summary: ChildCompleteProfile;
  sectionKeys?: (keyof ChildCompleteProfile)[];
  showHeading?: boolean;
}) {
  const { isViewer } = usePermissions();
  const viewer = isViewer();
  return (
    <section id={showHeading ? "summary" : undefined}>
      {showHeading && <h2 className="mb-4 text-xl font-bold">Complete profile summary</h2>}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sectionKeys.map((key) => (
          <article className="panel" key={key}>
            <h3 className="mb-3 font-bold text-slate-800">{titles[key]}</h3>
            <dl className="space-y-2">
              {safeEntries(key, summary[key], viewer).map(([label, value]) => (
                <div className="flex justify-between gap-4 text-sm" key={label}>
                  <dt className="capitalize text-slate-500">{label.replaceAll("_", " ")}</dt>
                  <dd className="text-right font-medium">{format(value)}</dd>
                </div>
              ))}
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

function safeEntries(section: keyof ChildCompleteProfile, values: Record<string, unknown>, viewer: boolean) {
  if (!viewer) return Object.entries(values);
  const restricted =
    section === "medical"
      ? new Set(["blood_group", "special_needs_flag", "chronic_disease_flag"])
      : section === "case_management"
        ? new Set(["risk_level", "welfare_status", "critical_incident_count"])
        : new Set<string>();
  return Object.entries(values).filter(([key]) => !restricted.has(key));
}

function format(value: unknown) {
  if (value === null || value === undefined || value === "") return "Not recorded";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ") || "Not recorded";
  return String(value);
}
