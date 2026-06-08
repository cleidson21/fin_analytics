"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
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
      {currentTab === "positions" && <PositionsTab />}
      {currentTab === "dividends" && <DividendsTab />}
      {currentTab === "categories" && <CategoriesTab />}
    </>
  );
}

export default function GovernanceDataPage() {
  return (
    <PageLayout
      title="Dados de Governança"
      hideTitle={true}
      breadcrumb={
        <div className="text-sm font-medium text-zinc-500 flex items-center gap-2">
          <Link href="/governance" className="hover:text-white transition-colors">Governança</Link>
          <span>/</span>
          <span className="text-zinc-300">Dados</span>
        </div>
      }
    >
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link 
          href="/governance"
          className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2 w-4 h-4" />
          Voltar para Dashboard
        </Link>
      </div>

      <Suspense fallback={<div className="text-zinc-400 p-8">Carregando abas...</div>}>
        <DataContent />
      </Suspense>
    </PageLayout>
  );
}
