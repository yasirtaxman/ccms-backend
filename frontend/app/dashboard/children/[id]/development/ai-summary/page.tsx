"use client";

import { use } from "react";
import { ChildDevelopmentAISummaryPanel } from "@/components/development/ChildDevelopmentAISummaryPanel";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ChildDevelopmentAISummaryPanel childId={Number(id)} />;
}
