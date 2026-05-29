import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { fetchFromAPI } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { CategoriesCard, type CategoryComparison } from "@/components/dashboard/CategoriesCard";
import { PacingCard, type PacingComparison } from "@/components/dashboard/PacingCard";
import { SummaryCards, type DashboardSummary } from "@/components/dashboard/SummaryCards";
import { PageLayout } from "@/components/layout/PageLayout";

export const dynamic = "force-dynamic";

function resolveReferenceMonth() {
  const envMonth = process.env.NEXT_PUBLIC_REFERENCE_MONTH?.trim();
  if (envMonth && /^\d{4}-\d{2}$/.test(envMonth)) {
    return envMonth;
  }

  return new Date().toISOString().slice(0, 7);
}

export default async function Home() {
  const referenceMonth = resolveReferenceMonth();

  const [summary, pacing, categories] = await Promise.all([
    fetchFromAPI<DashboardSummary>(`/dashboard/summary?month=${referenceMonth}`),
    fetchFromAPI<PacingComparison>(`/dashboard/pacing?month=${referenceMonth}`),
    fetchFromAPI<CategoryComparison[]>(`/dashboard/categories/comparison?month=${referenceMonth}`),
  ]);

  return (
    <PageLayout title="O seu motor financeiro está online." subtitle={`Dados de referência: ${referenceMonth}`}>
      <SummaryCards summary={summary} />

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <PacingCard pacing={pacing} />
      </div>

      <CategoriesCard categories={categories ?? []} />

      {summary ? (
        <section className="rounded-3xl border border-white/10 bg-gradient-to-r from-white/8 to-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-zinc-400">Patrimônio Consolidado</p>
              <p className="mt-3 text-3xl font-semibold tracking-tight">{formatCurrency(summary.net_worth)}</p>
            </div>

            <Link
              href="/wealth"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm font-medium text-zinc-50 transition hover:bg-white/15"
            >
              Acessar Investimentos
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      ) : null}
    </PageLayout>
  );
}
