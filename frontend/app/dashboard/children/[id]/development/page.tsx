"use client";

import { use } from "react";
import { ChildDevelopmentSummary } from "@/components/development/ChildDevelopmentSummary";
import { DevelopmentObservationsTable } from "@/components/development/DevelopmentObservationsTable";
import Link from "next/link";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Link className="secondary-button" href={`/dashboard/children/${id}/development/ai-summary`}>Open AI-Assisted Summary</Link>
      </div>
      <ChildDevelopmentSummary childId={Number(id)} />
      <DevelopmentObservationsTable />
    </div>
  );
}
