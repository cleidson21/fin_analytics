import { formatCurrency } from "@/lib/utils";

export interface PacingComparison {
  current_month: string;
  previous_month: string;
  current_expenses: string;
  previous_expenses: string;
  delta_percentage: string;
  trend: "up" | "down" | "stable";
  severity: "good" | "warning" | "danger";
  message: string;
}

export function PacingCard({ pacing }: { pacing: PacingComparison | null }) {
  if (!pacing) return <p>Sem dados.</p>;

  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
      <p className="text-sm text-zinc-400">Ritmo de Gastos</p>

      <div className="mt-4 space-y-3">
        <div className="flex items-end justify-between gap-4">
          <p className="text-3xl font-semibold tracking-tight text-zinc-50">
            {formatCurrency(pacing.current_expenses)}
          </p>
          <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-sm text-zinc-300">
            {pacing.delta_percentage}%
          </span>
        </div>

        <p className="text-sm leading-6 text-zinc-300">{pacing.message}</p>
      </div>
    </section>
  );
}