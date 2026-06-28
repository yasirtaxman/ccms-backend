"use client";

import { use } from "react";
import { SupportPlanDetail } from "@/components/development/SupportPlanDetail";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <SupportPlanDetail planId={Number(id)} />;
}
