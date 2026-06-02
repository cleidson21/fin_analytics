import Link from "next/link";
import { ArrowRight, ClipboardList } from "lucide-react";

import { PageLayout } from "@/components/layout/PageLayout";

export const dynamic = "force-dynamic";

export default function GovernanceHomePage() {
  return (
    <PageLayout title="Governança operacional" subtitle="Área de validação e importação do Pierre." hideTitle={true}>
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <p className="text-sm uppercase tracking-[0.2em] text-zinc-400">Operador único</p>
            <h2 className="text-2xl font-semibold text-white">Fluxo de importação controlado</h2>
            <p className="max-w-2xl text-sm text-zinc-300">
              Use a página de importação para colar apenas linhas novas do CSV do Pierre. O sistema mostra o estado
              operacional e a próxima linha esperada.
            </p>
          </div>

          <Link
            href="/governance/import"
            className="inline-flex items-center gap-2 rounded-full bg-emerald-400 px-4 py-2 text-sm font-medium text-emerald-950 transition hover:bg-emerald-300"
          >
            Abrir importação
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="mt-6 flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-zinc-300">
          <ClipboardList className="h-4 w-4 text-emerald-300" />
          <span>Revisão, quarentena e estado operacional ficam centralizados nesta área.</span>
        </div>
      </section>
    </PageLayout>
  );
}