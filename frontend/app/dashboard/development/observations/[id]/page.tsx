"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { Archive, CheckCircle2, Edit, Send, ShieldCheck } from "lucide-react";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import type { DevelopmentObservation } from "@/types/development";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const obsId = Number(id);
  const { hasPermission } = usePermissions();
  const [row, setRow] = useState<DevelopmentObservation | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = () => developmentApi.getObservation(obsId).then(setRow).catch((e) => setError(apiErrorMessage(e)));
  useEffect(() => {
    void load();
  }, [obsId]);

  const action = async (label: string, fn: () => Promise<DevelopmentObservation>) => {
    setError("");
    setMessage("");
    try {
      setRow(await fn());
      setMessage(label);
    } catch (e) {
      setError(apiErrorMessage(e));
    }
  };

  if (error && !row) return <div className="notice-error">{error}</div>;
  if (!row) return <div className="panel">Loading observation…</div>;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end">
        <div className="flex-1">
          <p className="eyebrow">Development Profile</p>
          <h1 className="page-title">Observation #{row.id}</h1>
          <p className="page-subtitle">Safe support and guidance record for current observation indicators.</p>
        </div>
        <Link className="secondary-button" href={`/dashboard/development/observations/${row.id}/edit`}><Edit size={16} />Edit</Link>
      </header>
      {error && <div className="notice-error">{error}</div>}
      {message && <div className="notice-success">{message}</div>}
      <section className="panel">
        <div className="grid gap-3 md:grid-cols-4">
          <Info label="Date" value={row.observation_date} />
          <Info label="Frequency" value={row.observation_frequency} />
          <Info label="Status" value={row.review_status} />
          <Info label="Urgent" value={row.urgent_flag ? "Needs review" : "No"} />
        </div>
        <p className="mt-5 text-sm text-slate-700">{row.general_summary || "No general summary recorded."}</p>
        <p className="mt-3 text-sm text-slate-600"><b>Recommended support:</b> {row.recommended_support || "Not recorded"}</p>
        {row.private_notes && <p className="mt-3 rounded-xl bg-slate-50 p-3 text-sm text-slate-600"><b>Private notes:</b> {row.private_notes}</p>}
      </section>
      <section className="panel">
        <h2 className="mb-4 text-lg font-bold">Indicator Responses</h2>
        {row.responses.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {row.responses.map((r) => <div className="rounded-xl border border-slate-200 p-3 text-sm" key={r.id}>
              <b>{r.indicator?.indicator_name || `Indicator ${r.indicator_id}`}</b>
              <p className="mt-1 text-slate-600">{String(r.value_text ?? r.value_number ?? r.value_boolean ?? (Array.isArray(r.value_json) ? r.value_json.join(", ") : "-"))}</p>
              {r.note && <p className="mt-1 text-slate-500">{r.note}</p>}
            </div>)}
          </div>
        ) : <div className="empty-card"><h2>No indicator responses</h2><p>This observation was saved without indicator details.</p></div>}
      </section>
      <div className="flex flex-wrap gap-2">
        {hasPermission("development.submit") && <button className="secondary-button" onClick={() => action("Observation submitted.", () => developmentApi.submit(row.id))}><Send size={16} />Submit</button>}
        {hasPermission("development.review") && <button className="secondary-button" onClick={() => action("Observation reviewed.", () => developmentApi.review(row.id, "Reviewed"))}><ShieldCheck size={16} />Review</button>}
        {hasPermission("development.close") && <button className="secondary-button" onClick={() => action("Observation closed.", () => developmentApi.close(row.id))}><CheckCircle2 size={16} />Close</button>}
        {hasPermission("development.delete") && <button className="secondary-button text-red-600" onClick={() => confirm("Archive this observation?") && action("Observation archived.", () => developmentApi.archive(row.id))}><Archive size={16} />Archive</button>}
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong>{value}</strong></div>;
}
