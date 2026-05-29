import { fetchFromAPI } from "@/lib/api";
import { AllocationChart } from "@/components/dashboard/AllocationChart";
import { CategoriesCard, type CategoryComparison } from "@/components/dashboard/CategoriesCard";
import { PacingCard, type PacingComparison } from "@/components/dashboard/PacingCard";
import { SummaryCards, type DashboardSummary } from "@/components/dashboard/SummaryCards";
import { PageLayout } from "@/components/layout/PageLayout";

interface AssetAllocation {
  asset_class: string;
  current_total: string;
}

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

  const [summary, pacing, allocation, categories] = await Promise.all([
    fetchFromAPI<DashboardSummary>(`/dashboard/summary?month=${referenceMonth}`),
    fetchFromAPI<PacingComparison>(`/dashboard/pacing?month=${referenceMonth}`),
    fetchFromAPI<AssetAllocation[]>("/investments/allocation"),
    fetchFromAPI<CategoryComparison[]>(`/dashboard/categories/comparison?month=${referenceMonth}`),
  ]);

  return (
    <PageLayout title="O seu motor financeiro está online." subtitle={`Dados de referência: ${referenceMonth}`}>
      <SummaryCards summary={summary} />

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <PacingCard pacing={pacing} />
        <AllocationChart data={allocation ?? []} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <CategoriesCard categories={categories ?? []} />
        <section className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-zinc-400 backdrop-blur">
          O Mapa de Calor Diário será renderizado aqui...
        </section>
      </div>
    </PageLayout>
  );
}
