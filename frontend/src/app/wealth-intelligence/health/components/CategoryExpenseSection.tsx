import type { CategoryExpenseSummary } from "../types";
import type { CategoryExpenseMetric } from "../types";
import { formatCurrency, formatPercent } from "../formatters";
import { getCategoryAccent } from "../visualTokens";
import { HealthPanel } from "./HealthPanel";

function CategoryRow({ item }: { item: CategoryExpenseMetric }) {
  const accent = getCategoryAccent(item.category);
  const visualShare = item.share_of_expenses === null
    ? 0
    : Math.max(0, Math.min(100, Number(item.share_of_expenses) * 100));

  return (
    <li className="group">
      <div className="mb-1.5 grid grid-cols-[28px_minmax(0,1fr)] items-baseline gap-x-2 gap-y-1 text-xs sm:grid-cols-[32px_minmax(0,1fr)_auto]">
        <span className="font-medium tabular-nums text-muted-foreground">#{item.rank}</span>
        <span className="flex min-w-0 items-center gap-2 font-medium text-foreground">
          <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full opacity-80" style={{ backgroundColor: accent.color }} />
          <span className="min-w-0 break-words [overflow-wrap:anywhere]">{item.category}</span>
        </span>
        <span className="col-start-2 flex flex-wrap items-center gap-x-2 tabular-nums text-foreground/90 sm:col-start-auto sm:justify-end">
          <span className="whitespace-nowrap">{formatCurrency(item.expense_total)}</span>
          <span className="whitespace-nowrap text-muted-foreground">{formatPercent(item.share_of_expenses)}</span>
        </span>
      </div>
      <div className="ml-9 h-1.5 overflow-hidden rounded-full bg-muted/45 sm:ml-10" aria-hidden="true">
        <div className="h-full rounded-full opacity-75 transition-[width] duration-500" style={{ width: `${visualShare}%`, backgroundColor: accent.color }} />
      </div>
    </li>
  );
}

export function CategoryExpenseSection({ summary }: { summary: CategoryExpenseSummary }) {
  const visibleCategories = summary.categories.slice(0, 5);
  const remainingCategories = summary.categories.slice(5);

  return (
    <HealthPanel
      title="Despesas por categoria"
      action={
        summary.top_category ? (
          <div className="text-right">
            <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Maior categoria</p>
            <div className="mt-1 flex max-w-[180px] items-center justify-end gap-1.5">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ backgroundColor: getCategoryAccent(summary.top_category.category).color }}
              />
              <p className="break-words text-xs font-semibold text-foreground [overflow-wrap:anywhere]">
                {summary.top_category.category}
              </p>
            </div>
          </div>
        ) : null
      }
    >
      {summary.categories.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-4 py-10 text-center text-sm text-muted-foreground">
          Não há despesas categorizadas para este período.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3 text-xs text-muted-foreground">
            <span>{summary.categories.length} categorias</span>
            <span className="rounded-full bg-muted/40 px-2.5 py-1 tabular-nums text-foreground/90">
              Total {formatCurrency(summary.total_expense)}
            </span>
          </div>

          <ol className="space-y-3" aria-label="Principais despesas por categoria">
            {visibleCategories.map((item) => <CategoryRow key={item.category} item={item} />)}
          </ol>
          {remainingCategories.length > 0 ? (
            <details className="group rounded-xl border border-border bg-muted/25">
              <summary className="cursor-pointer list-none px-3 py-2 text-xs font-medium text-muted-foreground marker:hidden">Ver demais categorias ({remainingCategories.length})</summary>
              <ol className="space-y-3 border-t border-border p-3" aria-label="Demais despesas por categoria">
                {remainingCategories.map((item) => <CategoryRow key={item.category} item={item} />)}
              </ol>
            </details>
          ) : null}
        </div>
      )}
    </HealthPanel>
  );
}
