"use client";

import { use } from "react";
import { DevelopmentAISummaryDetail } from "@/components/development/DevelopmentAISummaryDetail";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <DevelopmentAISummaryDetail summaryId={Number(id)} />;
}
