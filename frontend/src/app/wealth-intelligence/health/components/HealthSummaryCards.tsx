import { ArrowDownRight, ArrowUpRight, Landmark, Percent } from "lucide-react";
import type { ReactNode } from "react";

import type {
  CashflowSummary,
  FinancialTrendDirection,
  FinancialTrendResponse,
  GlobalFinancialTrendMetric,
} from "../types";
import {
  financialTone,
  formatCompactMonth,
  formatCurrency,
  formatPercent,
  formatSignedCurrency,
  formatSignedPercent,
  formatSignedPercentagePoints,
} from "../formatters";
import { healthMetricAccents } from "../visualTokens";

const cardBase =
  "relative overflow-hidden rounded-2xl border border-border bg-muted/35 p-4 shadow-lg shadow-black/10";

const trendTone: Record<FinancialTrendDirection, string> = {
  INCREASED: "border-sky-400/20 bg-sky-400/[0.09] text-sky-700 dark:text-sky-300",
  DECREASED: "border-violet-400/20 bg-violet-400/[0.09] text-violet-700 dark:text-violet-300",
  UNCHANGED: "border-border bg-muted/45 text-foreground/90",
  INSUFFICIENT_DATA: "border-amber-400/15 bg-amber-400/[0.06] text-warning-foreground",
};

interface SummaryCardProps {
  label: string;
  value: string;
  trend: ReactNode;
  tone: string;
  icon: ReactNode;
  accentBorder: string;
  iconTone: string;
}

function SummaryCard({ label, value, trend, tone, icon, accentBorder, iconTone }: SummaryCardProps) {
  return (
    <article className={`${cardBase} border-t-2 ${accentBorder}`}>
      <div className="absolute right-0 top-0 h-20 w-20 rounded-bl-full bg-muted/30" />
      <div className="relative flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
          <p className={`mt-1.5 break-words text-2xl font-semibold tabular-nums tracking-tight [overflow-wrap:anywhere] ${tone}`}>
            {value}
          </p>
        </div>
        <div className={`rounded-xl border p-2.5 ${iconTone}`}>{icon}</div>
      </div>
      <div className="relative mt-3 border-t border-border pt-3">{trend}</div>
    </article>
  );
}

function directionSymbol(direction: FinancialTrendDirection) {
  if (direction === "INCREASED") return "↑";
  if (direction === "DECREASED") return "↓";
  if (direction === "UNCHANGED") return "=";
  return "·";
}

function TrendKpi({
  metric,
  isSavingsRate = false,
}: {
  metric: GlobalFinancialTrendMetric | undefined;
  isSavingsRate?: boolean;
}) {
  if (!metric || metric.direction === "INSUFFICIENT_DATA") {
    return (
      <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold ${trendTone.INSUFFICIENT_DATA}`}>
        Sem histórico
      </span>
    );
  }

  const badgeValue = isSavingsRate
    ? formatSignedPercentagePoints(metric.absolute_delta)
    : formatSignedPercent(metric.percentage_delta);
  const absoluteDelta = isSavingsRate ? null : formatSignedCurrency(metric.absolute_delta);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold tabular-nums ${trendTone[metric.direction]}`}>
        <span aria-hidden="true">{directionSymbol(metric.direction)}</span>
        {badgeValue}
      </span>
      {absoluteDelta ? (
        <span className="text-xs font-semibold tabular-nums text-foreground/90">{absoluteDelta}</span>
      ) : null}
    </div>
  );
}

export function HealthSummaryCards({
  cashflow,
  trends,
}: {
  cashflow: CashflowSummary;
  trends: FinancialTrendResponse;
}) {
  const trendByMetric = new Map(trends.global.metrics.map((item) => [item.metric, item]));

  return (
    <section aria-labelledby="health-summary-title">
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 id="health-summary-title" className="text-base font-semibold text-foreground">Indicadores do mês</h2>
        <div className="flex flex-wrap gap-2 text-[11px] font-medium">
          <span className="rounded-full border border-border bg-muted/40 px-3 py-1.5 text-foreground/90">
            Período · {formatCompactMonth(cashflow.reference_month)}
          </span>
          <span className="rounded-full border border-sky-400/15 bg-sky-400/[0.07] px-3 py-1.5 text-sky-700 dark:text-sky-300">
            Comparação · {formatCompactMonth(trends.comparison_month)} → {formatCompactMonth(trends.trend_target_month)}
          </span>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Receitas"
          value={formatCurrency(cashflow.total_income)}
          trend={<TrendKpi metric={trendByMetric.get("total_income")} />}
          tone="text-success-foreground"
          icon={<ArrowUpRight aria-hidden="true" size={20} />}
          accentBorder={healthMetricAccents.income.border}
          iconTone={healthMetricAccents.income.icon}
        />
        <SummaryCard
          label="Despesas"
          value={formatCurrency(cashflow.total_expense)}
          trend={<TrendKpi metric={trendByMetric.get("total_expense")} />}
          tone="text-destructive"
          icon={<ArrowDownRight aria-hidden="true" size={20} />}
          accentBorder={healthMetricAccents.expense.border}
          iconTone={healthMetricAccents.expense.icon}
        />
        <SummaryCard
          label="Fluxo líquido"
          value={formatCurrency(cashflow.net_cashflow)}
          trend={<TrendKpi metric={trendByMetric.get("net_cashflow")} />}
          tone={financialTone(cashflow.net_cashflow)}
          icon={<Landmark aria-hidden="true" size={20} />}
          accentBorder={healthMetricAccents.net.border}
          iconTone={healthMetricAccents.net.icon}
        />
        <SummaryCard
          label="Taxa de poupança"
          value={formatPercent(cashflow.savings_rate)}
          trend={<TrendKpi metric={trendByMetric.get("savings_rate")} isSavingsRate />}
          tone={financialTone(cashflow.savings_rate)}
          icon={<Percent aria-hidden="true" size={20} />}
          accentBorder={healthMetricAccents.savings.border}
          iconTone={healthMetricAccents.savings.icon}
        />
      </div>
    </section>
  );
}
