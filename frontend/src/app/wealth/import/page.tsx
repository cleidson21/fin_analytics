"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { TopNav } from "@/components/layout/TopNav";

/**
 * Página de Importação de Investimentos
 * Status: PENDENTE — será implementada na Vertical Slice VS-08 (ImportCSV)
 * 
 * Spec: docs/37_USE_CASES.md (UC-08 ImportCSV)
 * Endpoints: POST /investments/import/cei, POST /investments/import/open-finance
 */
export default function WealthImportPage() {
  return (
    <>
      <PageLayout title="Importar Investimentos">
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <div className="text-4xl">📁</div>
          <h2 className="text-lg font-medium text-zinc-300">Em Construção</h2>
          <p className="text-sm text-zinc-500 max-w-sm">
            A importação de investimentos (CSV, CEI, Open Finance) será implementada na{" "}
            <span className="text-emerald-400 font-medium">Vertical Slice VS-08</span>.
          </p>
        </div>
      </PageLayout>
    </>
  );
}
