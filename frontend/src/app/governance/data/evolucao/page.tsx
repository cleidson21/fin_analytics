"use client";

import React from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { EvolucaoTab } from "@/components/governance/EvolucaoTab";
import { DataNav } from "@/components/governance/DataNav";

export default function GovernanceEvolucaoPage() {
  return (
    <PageLayout title="Dados - Evolução" hideTitle={true}>
      <DataNav />
      <EvolucaoTab />
    </PageLayout>
  );
}
