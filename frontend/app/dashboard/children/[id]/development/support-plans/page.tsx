"use client";

import { use } from "react";
import { ChildSupportPlansPanel } from "@/components/development/ChildSupportPlansPanel";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ChildSupportPlansPanel childId={Number(id)} />;
}
