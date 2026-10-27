"use client";

import Link from "next/link";
import {
  CalendarDays,
  ChevronDown,
  CircleDollarSign,
  Pencil,
  Target,
  Trash2,
} from "lucide-react";

import { GOAL_STATUS_LABELS, GOAL_TYPE_LABELS, type Goal } from "./types";

const BRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const PERCENT = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const STATUS_CONFIG: Record<Goal["status"], { className: string }> = {
  ACTIVE: { className: "border-emerald-400/20 bg-emerald-400/10 text-success-foreground" },
  PAUSED: { className: "border-amber-400/20 bg-amber-400/10 text-warning-foreground" },
  ACHIEVED: { className: "border-sky-400/20 bg-sky-400/10 text-sky-700 dark:text-sky-300" },
  CANCELLED: { className: "border-border bg-unavailable/10 text-muted-foreground" },
};

const PRIORITY_LABELS: Record<number, string> = {
  1: "Prioridade 1",
  2: "Prioridade 2",
  3: "Prioridade 3",
  4: "Prioridade 4",
  5: "Prioridade 5",
};

interface GoalCardProps {
  goal: Goal;
  onEdit: (goal: Goal) => void;
  onDelete: (goal: Goal) => void;
}

export function GoalCard({ goal, onEdit, onDelete }: GoalCardProps) {
  const status = STATUS_CONFIG[goal.status];
  const hasCurrentAmount = goal.current_amount !== null && goal.current_amount !== undefined;
  const hasGovernedProgress = hasCurrentAmount
    && goal.progress_pct !== null
    && goal.progress_pct !== undefined;
  const visualProgress = hasGovernedProgress
    ? Math.min(100, Math.max(0, goal.progress_pct as number))
    : null;
  const progressLabel = hasGovernedProgress
    ? PERCENT.format((goal.progress_pct as number) / 100)
    : null;

  return (
    <article className="flex min-w-0 flex-col rounded-2xl border border-border bg-muted/30 p-4 transition hover:border-border hover:bg-muted/40 sm:p-5">
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.13em] text-muted-foreground">
            {GOAL_TYPE_LABELS[goal.goal_type]}
          </p>
          <h2 className="mt-1 truncate text-base font-semibold text-foreground" title={goal.name}>
            {goal.name}
          </h2>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          {goal.priority ? (
            <span className="rounded-full border border-border px-2 py-1 text-[10px] font-semibold text-muted-foreground">
              {PRIORITY_LABELS[goal.priority]}
            </span>
          ) : null}
          <span className={`rounded-full border px-2 py-1 text-[10px] font-semibold ${status.className}`}>
            {GOAL_STATUS_LABELS[goal.status]}
          </span>
        </div>
      </header>

      <div className="mt-5 min-h-11">
        {hasGovernedProgress && visualProgress !== null && progressLabel ? (
          <div>
            <div className="mb-2 flex items-end justify-between gap-3">
              <span className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Progresso</span>
              <span className="text-sm font-semibold tabular-nums text-success-foreground">{progressLabel}</span>
            </div>
            <div
              role="progressbar"
              aria-label={`Progresso da meta ${goal.name}`}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={visualProgress}
              aria-valuetext={progressLabel}
              className="h-2.5 overflow-hidden rounded-full bg-muted/55"
            >
              <div
                className={`h-full rounded-full transition-[width] motion-reduce:transition-none ${visualProgress >= 100 ? "bg-emerald-400" : "bg-gradient-to-r from-sky-400 to-emerald-400"}`}
                style={{ width: `${visualProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg border border-dashed border-border px-3 py-2 text-xs text-muted-foreground">
            <Target aria-hidden="true" className="size-3.5" />
            Progresso ainda não disponível
          </div>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-2 border-t border-border pt-4 text-xs sm:grid-cols-4">
        <div className="min-w-0 rounded-lg bg-muted/30 px-3 py-2.5">
          <dt className="text-[10px] uppercase tracking-[0.1em] text-muted-foreground">Valor atual</dt>
          <dd className="mt-1 truncate font-medium tabular-nums text-foreground" title={hasCurrentAmount ? BRL.format(goal.current_amount as number) : "Não informado"}>
            {hasCurrentAmount ? BRL.format(goal.current_amount as number) : "Não informado"}
          </dd>
        </div>
        <div className="min-w-0 rounded-lg bg-muted/30 px-3 py-2.5">
          <dt className="flex items-center gap-1 text-[10px] uppercase tracking-[0.1em] text-muted-foreground"><CircleDollarSign aria-hidden="true" className="size-3" />Aporte</dt>
          <dd className="mt-1 truncate font-medium tabular-nums text-foreground/90" title={goal.monthly_contribution !== null && goal.monthly_contribution !== undefined ? `${BRL.format(goal.monthly_contribution)}/mês` : "Não informado"}>
            {goal.monthly_contribution !== null && goal.monthly_contribution !== undefined ? `${BRL.format(goal.monthly_contribution)}/mês` : "Não informado"}
          </dd>
        </div>
        <div className="min-w-0 rounded-lg bg-muted/30 px-3 py-2.5">
          <dt className="flex items-center gap-1 text-[10px] uppercase tracking-[0.1em] text-muted-foreground"><CalendarDays aria-hidden="true" className="size-3" />Data-alvo</dt>
          <dd className="mt-1 truncate font-medium tabular-nums text-foreground/90">
            {goal.target_date ? new Date(`${goal.target_date}T00:00:00`).toLocaleDateString("pt-BR") : "Não informada"}
          </dd>
        </div>
        <div className="min-w-0 rounded-lg border border-sky-300/15 bg-sky-300/[0.07] px-3 py-2.5">
          <dt className="text-[10px] uppercase tracking-[0.1em] text-sky-700 dark:text-sky-300">Objetivo</dt>
          <dd className="mt-1 truncate font-semibold tabular-nums text-sky-700 dark:text-sky-300" title={BRL.format(goal.target_amount)}>{BRL.format(goal.target_amount)}</dd>
        </div>
      </dl>

      {goal.description ? (
        <details className="group mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 font-medium text-muted-foreground hover:text-foreground">
            Detalhes da meta
            <ChevronDown aria-hidden="true" className="size-4 transition-transform group-open:rotate-180" />
          </summary>
          <p className="mt-2 leading-5 text-muted-foreground">{goal.description}</p>
        </details>
      ) : null}

      <footer className="mt-3 flex flex-wrap justify-end gap-2 border-t border-border pt-3">
        <Link
          href={`/wealth-intelligence/planning?intent=objective&task=goals&goal=${encodeURIComponent(goal.id)}`}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-violet-300/20 bg-violet-300/[0.07] px-3 py-2 text-xs font-semibold text-violet-700 transition hover:bg-violet-300/[0.12] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/50 dark:text-violet-300"
        >
          <Target aria-hidden="true" className="size-3.5" />
          Simular esta meta
        </Link>
        <button
          type="button"
          onClick={() => onEdit(goal)}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-sky-300/20 bg-sky-300/[0.06] px-3 py-2 text-xs font-semibold text-sky-700 dark:text-sky-300 transition hover:bg-sky-300/[0.12] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/50"
        >
          <Pencil aria-hidden="true" className="size-3.5" />
          Editar
        </button>
        <button
          type="button"
          onClick={() => onDelete(goal)}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-300/15 bg-rose-300/[0.04] px-3 py-2 text-xs font-semibold text-destructive transition hover:bg-rose-300/[0.10] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-300/50"
        >
          <Trash2 aria-hidden="true" className="size-3.5" />
          Excluir
        </button>
      </footer>
    </article>
  );
}
