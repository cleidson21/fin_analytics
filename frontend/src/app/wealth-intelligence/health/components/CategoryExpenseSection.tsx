import type { CategoryExpenseSummary } from "../types";
import { formatCurrency, formatPercent } from "../formatters";
import { getCategoryAccent } from "../visualTokens";
import { HealthPanel } from "./HealthPanel";

export function CategoryExpenseSection({ summary }: { summary: CategoryExpenseSummary }) {
  return (
    <HealthPanel
      title="Despesas por categoria"
      action={
        summary.top_category ? (
          <div className="text-right">
            <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-zinc-600">Maior categoria</p>
            <div className="mt-1 flex max-w-[180px] items-center justify-end gap-1.5">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ backgroundColor: getCategoryAccent(summary.top_category.category).color }}
              />
              <p className="break-words text-xs font-semibold text-zinc-200 [overflow-wrap:anywhere]">
                {summary.top_category.category}
              </p>
            </div>
          </div>
        ) : null
      }
    >
      {summary.categories.length === 0 ? (
        <div className="rounded-xl border border-dashed border-white/10 px-4 py-10 text-center text-sm text-zinc-500">
          Não há despesas categorizadas para este período.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] pb-3 text-xs text-zinc-500">
            <span>{summary.categories.length} categorias</span>
            <span className="rounded-full bg-white/[0.04] px-2.5 py-1 tabular-nums text-zinc-300">
              Total {formatCurrency(summary.total_expense)}
            </span>
          </div>

          <ol className="space-y-3" aria-label="Ranking de despesas por categoria">
            {summary.categories.map((item) => {
              const accent = getCategoryAccent(item.category);
              const visualShare = item.share_of_expenses === null
                ? 0
                : Math.max(0, Math.min(100, Number(item.share_of_expenses) * 100));

              return (
                <li key={item.category} className="group">
                  <div className="mb-1.5 grid grid-cols-[28px_minmax(0,1fr)] items-baseline gap-x-2 gap-y-1 text-xs sm:grid-cols-[32px_minmax(0,1fr)_auto]">
                    <span className="font-medium tabular-nums text-zinc-600">#{item.rank}</span>
                    <span className="flex min-w-0 items-center gap-2 font-medium text-zinc-200">
                      <span
                        aria-hidden="true"
                        className="h-1.5 w-1.5 shrink-0 rounded-full opacity-80"
                        style={{ backgroundColor: accent.color }}
                      />
                      <span className="min-w-0 break-words [overflow-wrap:anywhere]">{item.category}</span>
                    </span>
                    <span className="col-start-2 flex flex-wrap items-center gap-x-2 tabular-nums text-zinc-300 sm:col-start-auto sm:justify-end">
                      <span className="whitespace-nowrap">{formatCurrency(item.expense_total)}</span>
                      <span className="whitespace-nowrap text-zinc-600">{formatPercent(item.share_of_expenses)}</span>
                    </span>
                  </div>
                  <div className="ml-9 h-1.5 overflow-hidden rounded-full bg-white/[0.05] sm:ml-10" aria-hidden="true">
                    <div
                      className="h-full rounded-full opacity-75 transition-[width] duration-500"
                      style={{ width: `${visualShare}%`, backgroundColor: accent.color }}
                    />
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </HealthPanel>
  );
}
