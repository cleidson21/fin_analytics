import { Suspense } from "react";
import { PageLayout } from "@/components/layout/PageLayout";

import { WealthHomeExperience } from "./components/WealthHomeExperience";

export default function WealthIntelligenceDashboard() {
  return (
    <PageLayout title="Visão geral — Inteligência Patrimonial" hideTitle>
      <Suspense fallback={<div className="min-h-64 animate-pulse rounded-[2rem] border border-border bg-muted/30" />}>
        <WealthHomeExperience />
      </Suspense>
    </PageLayout>
  );
}
