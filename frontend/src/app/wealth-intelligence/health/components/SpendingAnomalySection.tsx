import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  History,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  SpendingAnomalyEvaluation,
  SpendingAnomalyStatus,
  SpendingAnomalySummary,
} from "../types";
import { formatCurrency, formatRatio, formatReferenceMonth } from "../formatters";
import { getCategoryAccent } from "../visualTokens";
import { HealthPanel } from "./HealthPanel";

const statusPresentation: Record<
  SpendingAnomalyStatus,
  { label: string; icon: LucideIcon; tone: string }
> = {
  NORMAL: {
    label: "Normal",
    icon: CheckCircle2,
    tone: "border-emerald-400/15 bg-emerald-400/[0.07] text-success-foreground",
  },
  SPIKE: {
    label: "Pico de despesa",
    icon: TrendingUp,
    tone: "border-amber-400/20 bg-amber-400/[0.1] text-warning-foreground",
  },
  NEW_EXPENSE: {
    label: "Nova despesa",
    icon: Sparkles,
    tone: "border-amber-400/20 bg-amber-400/[0.1] text-warning-foreground",
  },
  INSUFFICIENT_HISTORY: {
    label: "Histórico insuficiente",
    icon: History,
    tone: "border-border bg-muted/45 text-muted-foreground",
  },
  BELOW_BASELINE_FLOOR: {
    label: "Abaixo do piso de referência",
    icon: CircleHelp,
    tone: "border-border bg-muted/45 text-muted-foreground",
  },
  NEW_EXPENSE_BELOW_THRESHOLD: {
    label: "Nova despesa abaixo do limite",
    icon: CircleHelp,
    tone: "border-border bg-muted/45 text-muted-foreground",
  },
};

function StatusBadge({ status }: { status: SpendingAnomalyStatus }) {
  const presentation = statusPresentation[status];
  const Icon = presentation.icon;

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-semibold ${presentation.tone}`}
    >
      <Icon aria-hidden="true" size={12} />
      {presentation.label}
    </span>
  );
}

function CategoryIdentity({ category }: { category: string }) {
  const accent = getCategoryAccent(category);

  return (
    <span
      aria-hidden="true"
      className="mt-1.5 h-2 w-2 shrink-0 rounded-full opacity-90"
      style={{ backgroundColor: accent.color }}
    />
  );
}

function EvaluationFacts({ evaluation }: { evaluation: SpendingAnomalyEvaluation }) {
  return (
    <dl className="mt-4 grid grid-cols-2 gap-2">
      <div className="min-w-0 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
        <dt className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Atual</dt>
        <dd className="mt-1 whitespace-nowrap text-base font-semibold tabular-nums text-foreground">
          {formatCurrency(evaluation.current_expense)}
        </dd>
      </div>
      <div className="min-w-0 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
        <dt className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Referência</dt>
        <dd className="mt-1 whitespace-nowrap text-sm font-semibold tabular-nums text-foreground/90">
          {formatCurrency(evaluation.baseline_reference)}
        </dd>
      </div>
      <div className="min-w-0 rounded-lg border border-amber-400/10 bg-amber-400/[0.035] px-3 py-2.5">
        <dt className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Razão</dt>
        <dd className="mt-1 whitespace-nowrap text-sm font-semibold tabular-nums text-warning-foreground">
          {formatRatio(evaluation.ratio)}
        </dd>
      </div>
      <div className="min-w-0 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
        <dt className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Base</dt>
        <dd className="mt-1 text-sm font-semibold tabular-nums text-foreground/90">
          {evaluation.baseline_months_used.length || "—"}
          {evaluation.baseline_months_used.length > 0 ? (
            <span className="ml-1 text-[10px] font-normal text-muted-foreground">meses</span>
          ) : null}
        </dd>
      </div>
    </dl>
  );
}

function AnomalyCard({ item }: { item: SpendingAnomalyEvaluation }) {
  return (
    <article className="rounded-xl border border-amber-400/15 bg-amber-400/[0.045] p-4 shadow-sm shadow-black/10">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <CategoryIdentity category={item.category} />
          <h3 className="min-w-0 break-words text-sm font-semibold text-foreground [overflow-wrap:anywhere]">
            {item.category}
          </h3>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <EvaluationFacts evaluation={item} />

      {item.baseline_months_used.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-border pt-3">
          <span className="mr-1 text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Período base</span>
          {item.baseline_months_used.map((month) => (
            <span
              key={month}
              className="rounded-full border border-border bg-muted/25 px-2 py-0.5 text-[10px] tabular-nums text-muted-foreground"
            >
              {formatReferenceMonth(month, true)}
            </span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function SpendingAnomalySection({ summary }: { summary: SpendingAnomalySummary }) {
  if (summary.global_status === "INSUFFICIENT_BASELINE") {
    return (
      <HealthPanel title="Sinais de despesa">
        <div className="flex items-start gap-3 rounded-xl border border-amber-400/15 bg-amber-400/[0.06] p-4">
          <span className="rounded-lg border border-amber-400/15 bg-amber-400/[0.08] p-2 text-warning-foreground">
            <History aria-hidden="true" size={18} />
          </span>
          <div>
            <p className="text-sm font-semibold text-warning-foreground">Dados históricos insuficientes</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              São necessários três meses fechados contínuos para esta avaliação.
            </p>
          </div>
        </div>
      </HealthPanel>
    );
  }

  const nonAnomalies = summary.evaluations.filter(
    (item) => item.status !== "SPIKE" && item.status !== "NEW_EXPENSE",
  );

  return (
    <HealthPanel
      title="Sinais de despesa"
      action={
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
            summary.anomalies.length > 0
              ? "border-amber-400/20 bg-amber-400/[0.08] text-warning-foreground"
              : "border-emerald-400/20 bg-emerald-400/[0.08] text-success-foreground"
          }`}
        >
          {summary.anomalies.length > 0 ? (
            <AlertTriangle aria-hidden="true" size={12} />
          ) : (
            <CheckCircle2 aria-hidden="true" size={12} />
          )}
          {summary.anomalies.length} {summary.anomalies.length === 1 ? "sinal" : "sinais"}
        </span>
      }
    >
      {summary.anomalies.length === 0 ? (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-400/15 bg-emerald-400/[0.045] p-4">
          <span className="rounded-lg border border-emerald-400/15 bg-emerald-400/[0.07] p-2 text-success-foreground">
            <CheckCircle2 aria-hidden="true" size={18} />
          </span>
          <p className="text-sm font-medium text-foreground/90">Nenhum sinal identificado neste período.</p>
        </div>
      ) : (
        <div className="grid gap-3 xl:grid-cols-2">
          {summary.anomalies.map((item) => (
            <AnomalyCard key={`${item.category}-${item.status}`} item={item} />
          ))}
        </div>
      )}

      {nonAnomalies.length > 0 ? (
        <details className="group mt-4 rounded-xl border border-border bg-muted/25">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 marker:hidden">
            <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <CircleHelp aria-hidden="true" size={15} />
              Outras avaliações ({nonAnomalies.length})
            </span>
            <ChevronDown aria-hidden="true" className="text-muted-foreground transition group-open:rotate-180" size={15} />
          </summary>
          <div className="divide-y divide-border border-t border-border">
            {nonAnomalies.map((item) => (
              <div
                key={`${item.category}-${item.status}`}
                className="grid gap-2 px-4 py-3 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center sm:gap-4"
              >
                <span className="flex min-w-0 items-start gap-2.5">
                  <CategoryIdentity category={item.category} />
                  <span className="break-words text-xs font-medium text-foreground/90 [overflow-wrap:anywhere]">
                    {item.category}
                  </span>
                </span>
                <span className="text-xs font-semibold tabular-nums text-foreground/90">
                  {formatCurrency(item.current_expense)}
                </span>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </HealthPanel>
  );
}
