"use client";

import React from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { PositionsTab } from "@/components/governance/PositionsTab";

import { DataNav } from "@/components/governance/DataNav";

export default function GovernancePositionsPage() {
  return (
    <PageLayout title="Dados - Posições" hideTitle={true}>
      <DataNav />
      <PositionsTab />
    </PageLayout>
  );
}
