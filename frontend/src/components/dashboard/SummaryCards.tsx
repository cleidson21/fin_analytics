import { formatCurrency } from "@/lib/utils";

export interface DashboardSummary {
  net_worth: string;
  income: string;
  expenses: string;
  balance: string;
}

export function SummaryCards({ summary }: { summary: DashboardSummary | null }) {
  if (!summary) return null;

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
        <p className="text-sm text-zinc-400">Patrimônio Total</p>
        <p className="mt-4 text-3xl font-semibold tracking-tight">
          {formatCurrency(summary.net_worth)}
        </p>
      </article>

      <article className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
        <p className="text-sm text-zinc-400">Receitas</p>
        <p className="mt-4 text-3xl font-semibold tracking-tight text-emerald-300">
          {formatCurrency(summary.income)}
        </p>
      </article>

      <article className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
        <p className="text-sm text-zinc-400">Despesas</p>
        <p className="mt-4 text-3xl font-semibold tracking-tight text-rose-300">
          {formatCurrency(summary.expenses)}
        </p>
      </article>

      <article className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
        <p className="text-sm text-zinc-400">Saldo Líquido</p>
        <p className="mt-4 text-3xl font-semibold tracking-tight text-cyan-300">
          {formatCurrency(summary.balance)}
        </p>
      </article>
    </section>
  );
}