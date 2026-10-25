import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronDown,
  CircleHelp,
  Equal,
  LogOut,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  CategoryFinancialTrend,
  CategoryTrendDirection,
  FinancialTrendResponse,
} from "../types";
import {
  formatCompactMonth,
  formatCurrency,
  formatSignedCurrency,
  formatSignedPercent,
} from "../formatters";
import { getCategoryAccent } from "../visualTokens";
import { HealthPanel } from "./HealthPanel";

const directionPresentation: Record<
  CategoryTrendDirection,
  { label: string; icon: LucideIcon; tone: string }
> = {
  INCREASED: {
    label: "Aumentou",
    icon: ArrowUpRight,
    tone: "border-sky-400/20 bg-sky-400/[0.09] text-sky-700 dark:text-sky-300",
  },
  DECREASED: {
    label: "Reduziu",
    icon: ArrowDownRight,
    tone: "border-violet-400/20 bg-violet-400/[0.09] text-violet-700 dark:text-violet-300",
  },
  UNCHANGED: {
    label: "Estável",
    icon: Equal,
    tone: "border-border bg-muted/45 text-foreground/90",
  },
  NEW: {
    label: "Nova",
    icon: Sparkles,
    tone: "border-emerald-400/20 bg-emerald-400/[0.08] text-success-foreground",
  },
  DISAPPEARED: {
    label: "Saiu",
    icon: LogOut,
    tone: "border-rose-400/20 bg-rose-400/[0.08] text-destructive",
  },
  INSUFFICIENT_DATA: {
    label: "Dados insuficientes",
    icon: CircleHelp,
    tone: "border-amber-400/15 bg-amber-400/[0.06] text-warning-foreground",
  },
};

function StatusBadge({ direction }: { direction: CategoryTrendDirection }) {
  const presentation = directionPresentation[direction];
  const Icon = presentation.icon;

  return (
    <span className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-semibold ${presentation.tone}`}>
      <Icon aria-hidden="true" size={12} />
      {presentation.label}
    </span>
  );
}

function TrendItem({ item }: { item: CategoryFinancialTrend }) {
  const isDisappeared = item.direction === "DISAPPEARED";
  const amount = isDisappeared ? item.previous_expense : item.current_expense;
  const accent = getCategoryAccent(item.category);

  return (
    <li
      className="rounded-xl border border-l-2 border-border bg-muted/25 p-3.5"
      style={{ borderLeftColor: accent.color }}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="min-w-0 break-words text-sm font-semibold text-foreground [overflow-wrap:anywhere]">
          {item.category}
        </h3>
        <StatusBadge direction={item.direction} />
      </div>
      <div className="mt-3 flex flex-wrap items-end gap-x-5 gap-y-2 border-t border-border pt-3">
        <div>
          <p className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {isDisappeared ? "Anterior" : "Atual"}
          </p>
          <p className="mt-0.5 text-base font-semibold tabular-nums text-foreground">{formatCurrency(amount)}</p>
        </div>
        {item.absolute_delta !== null ? (
          <div>
            <p className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Variação</p>
            <p className="mt-0.5 text-sm font-semibold tabular-nums text-foreground/90">
              {formatSignedCurrency(item.absolute_delta)}
            </p>
          </div>
        ) : null}
        {item.percentage_delta !== null ? (
          <div>
            <p className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Relativa</p>
            <p className="mt-0.5 text-sm font-semibold tabular-nums text-foreground/90">
              {formatSignedPercent(item.percentage_delta)}
            </p>
          </div>
        ) : null}
      </div>
    </li>
  );
}

export function CategoryTrendSection({ trends }: { trends: FinancialTrendResponse }) {
  const { categories } = trends;
  const visibleItems = categories.items.slice(0, 6);
  const remainingItems = categories.items.slice(6);
  const period = `${formatCompactMonth(trends.comparison_month)} → ${formatCompactMonth(trends.trend_target_month)}`;

  return (
    <HealthPanel
      title="Tendências por categoria"
      action={
        <span className="rounded-full border border-sky-400/15 bg-sky-400/[0.07] px-3 py-1.5 text-[11px] font-medium text-sky-700 dark:text-sky-300">
          {period}
        </span>
      }
    >
      {categories.status === "INSUFFICIENT_DATA" ? (
        <div className="rounded-xl border border-dashed border-border px-4 py-7 text-center text-sm text-muted-foreground">
          Sem histórico comparável para este período.
        </div>
      ) : (
        <div>
          <ol className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-3" aria-label="Tendências por categoria">
            {visibleItems.map((item) => <TrendItem key={item.category} item={item} />)}
          </ol>
          {remainingItems.length > 0 ? (
            <details className="group mt-3 rounded-xl border border-border bg-muted/25">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-xs font-medium text-foreground/90 marker:hidden">
                Ver todas as categorias ({categories.items.length})
                <ChevronDown aria-hidden="true" className="text-muted-foreground transition group-open:rotate-180" size={15} />
              </summary>
              <ol className="grid gap-2.5 border-t border-border p-3 md:grid-cols-2 xl:grid-cols-3" aria-label="Demais tendências por categoria">
                {remainingItems.map((item) => <TrendItem key={item.category} item={item} />)}
              </ol>
            </details>
          ) : null}
        </div>
      )}
    </HealthPanel>
  );
}
