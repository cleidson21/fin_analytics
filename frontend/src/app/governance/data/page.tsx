"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { PageLayout } from "@/components/layout/PageLayout";
import { DataTabsNav } from "@/components/governance/DataTabsNav";
import { TransactionsTab } from "@/components/governance/TransactionsTab";
import { PositionsTab } from "@/components/governance/PositionsTab";
import { DividendsTab } from "@/components/governance/DividendsTab";
import { CategoriesTab } from "@/components/governance/CategoriesTab";

function DataContent() {
  const searchParams = useSearchParams();
  const currentTab = searchParams.get("tab") || "transactions";

  return (
    <>
      <DataTabsNav />
      {currentTab === "transactions" && <TransactionsTab />}
      {currentTab === "positions"    && <PositionsTab />}
      {currentTab === "dividends"    && <DividendsTab />}
      {currentTab === "categories"   && <CategoriesTab />}
    </>
  );
}

export default function GovernanceDataPage() {
  return (
    <PageLayout title="MyProfit" hideTitle={true}>
      <Suspense fallback={<div className="text-zinc-400 p-8">Carregando...</div>}>
        <DataContent />
      </Suspense>
    </PageLayout>
  );
}
