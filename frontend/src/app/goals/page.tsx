import { PageLayout } from "@/components/layout/PageLayout";

export default function GoalsPage() {
  return (
    <PageLayout title="Metas" subtitle="Objetivos e marcos financeiros.">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 text-sm text-zinc-400 backdrop-blur">
        Módulo de simulações e metas de aportes em desenvolvimento para os Sprints futuros.
      </section>
    </PageLayout>
  );
}
