"use client";

import React from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { DividendsTab } from "@/components/governance/DividendsTab";

import { DataNav } from "@/components/governance/DataNav";

export default function GovernanceDividendsPage() {
  return (
    <PageLayout title="Dados - Proventos" hideTitle={true}>
      <DataNav />
      <DividendsTab />
    </PageLayout>
  );
}
