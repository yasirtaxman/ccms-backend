"use client";

import { use } from "react";
import { ChildDevelopmentSummary } from "@/components/development/ChildDevelopmentSummary";
import { DevelopmentObservationsTable } from "@/components/development/DevelopmentObservationsTable";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <div className="space-y-6">
      <ChildDevelopmentSummary childId={Number(id)} />
      <DevelopmentObservationsTable />
    </div>
  );
}
