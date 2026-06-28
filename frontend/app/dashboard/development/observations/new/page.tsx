"use client";

import { useSearchParams } from "next/navigation";
import { DevelopmentObservationForm } from "@/components/development/DevelopmentObservationForm";

export default function Page() {
  const params = useSearchParams();
  const child = params.get("child_id");
  return <DevelopmentObservationForm childId={child ? Number(child) : undefined} />;
}
