"use client";

import { use } from "react";
import { SupportPlanForm } from "@/components/development/SupportPlanForm";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <SupportPlanForm childId={Number(id)} />;
}
