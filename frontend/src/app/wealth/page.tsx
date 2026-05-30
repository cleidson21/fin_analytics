import { PageLayout } from "@/components/layout/PageLayout";
import { resolveMonth } from "@/lib/period";

type SearchParams = Record<string, string | string[] | undefined>;

export default async function WealthPage({ searchParams }: { searchParams?: Promise<SearchParams> | SearchParams }) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const month = resolveMonth(resolvedSearchParams.month);

  return (
    <PageLayout title="Patrimônio" subtitle={`Visão consolidada da camada de riqueza.${month ? ` Período: ${month}.` : ""}`}>
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-zinc-400 backdrop-blur">
        Conteúdo de patrimônio em construção.
      </section>
    </PageLayout>
  );
}
