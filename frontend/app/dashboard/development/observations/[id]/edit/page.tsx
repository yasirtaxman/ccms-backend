"use client";

import { use } from "react";
import { DevelopmentObservationForm } from "@/components/development/DevelopmentObservationForm";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <DevelopmentObservationForm observationId={Number(id)} />;
}
