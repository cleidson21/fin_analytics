import type { ReactNode } from "react";
import { GitCompareArrows, TrendingUp } from "lucide-react";
import {
  formatAnnualRateDecimalString,
  formatBRDate,
  formatBRLDecimalString,
  formatMonthlyRateDecimalString,
  formatReferenceMonth,
} from "@/lib/planningLocale";
import type {
  ForwardProjectionResponse,
  GoalPlanningResponse,
  InitialWealthFact,
  RequiredContributionResponse,
  ScenarioComparisonEntry,
  ScenarioComparisonResponse,
  TargetAchievementResult,
} from "@/lib/planning";

import { ProjectionChart, ScenarioComparisonChart } from "./PlanningCharts";

type ValueKind = "money" | "annualRate" | "monthlyRate" | "date" | "months" | "text";
type MetricProps = { label: string; value: string | number | null; kind?: ValueKind; emphasis?: boolean };

// Semantic accent edges per intention: violet=simulate, emerald=target-achieved, amber=required, sky=comparison, zinc=neutral goal
type HeroAccent = "violet" | "emerald" | "amber" | "sky" | "zinc";

const statusLabels: Record<string, string> = {
  ALREADY_ACHIEVED: "Já alcançada",
  ACHIEVED: "Alcançada",
  UNREACHABLE: "Inatingível nas premissas atuais",
  NOT_REACHED_WITHIN_HORIZON: "Não alcançada no horizonte",
  ZERO_CONTRIBUTION_REQUIRED: "Sem aporte adicional necessário",
  SOLVED: "Aporte calculado",
  IMPOSSIBLE_HORIZON: "Impossível no horizonte",
  OUT_OF_SUPPORTED_RANGE: "Fora do intervalo suportado",
  PROJECTED_EARLY: "Projetada antes do prazo",
  PROJECTED_ON_TIME: "Projetada dentro do prazo",
  PROJECTED_LATE: "Projetada após o prazo",
  INSUFFICIENT_DATA: "Dados insuficientes",
  NOT_APPLICABLE: "Não aplicável",
};

// Status badge semantic colors — no pink/rose for PROJECTED_LATE
const statusBadgeStyles: Record<string, string> = {
  ALREADY_ACHIEVED: "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
  ACHIEVED: "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
  ZERO_CONTRIBUTION_REQUIRED: "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
  PROJECTED_EARLY: "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
  PROJECTED_ON_TIME: "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
  PROJECTED_LATE: "border-amber-500/25 bg-amber-500/10 text-amber-400",
  SOLVED: "border-border bg-muted/40 text-muted-foreground",
  NOT_APPLICABLE: "border-border bg-muted/40 text-muted-foreground",
  INSUFFICIENT_DATA: "border-border bg-muted/40 text-muted-foreground",
  UNREACHABLE: "border-amber-500/25 bg-amber-500/10 text-amber-400",
  NOT_REACHED_WITHIN_HORIZON: "border-amber-500/25 bg-amber-500/10 text-amber-400",
  IMPOSSIBLE_HORIZON: "border-amber-500/25 bg-amber-500/10 text-amber-400",
  OUT_OF_SUPPORTED_RANGE: "border-amber-500/25 bg-amber-500/10 text-amber-400",
};

// Hero accent edge: 2px left border, semantically minimal
const heroAccentEdge: Record<HeroAccent, string> = {
  violet: "border-l-2 border-l-violet-500/35",
  emerald: "border-l-2 border-l-emerald-500/35",
  amber: "border-l-2 border-l-amber-500/35",
  sky: "border-l-2 border-l-sky-500/30",
  zinc: "border-l-2 border-l-zinc-600/40",
};

function displayValue(value: string | number | null, kind: ValueKind) {
  if (value === null) return "—";
  if (kind === "money") return formatBRLDecimalString(String(value));
  if (kind === "annualRate") return formatAnnualRateDecimalString(String(value));
  if (kind === "monthlyRate") return formatMonthlyRateDecimalString(String(value));
  if (kind === "date") return typeof value === "string" ? formatBRDate(value) : "—";
  if (kind === "months") return `${value} ${value === 1 ? "mês" : "meses"}`;
  return String(value);
}

// Secondary metrics: no individual card borders — editorial typographic grid
function Metric({ label, value, kind = "text", emphasis = false }: MetricProps) {
  return (
    <div className={`py-2.5 ${emphasis ? "sm:col-span-2" : ""}`}>
      <p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">{label}</p>
      <p className={`mt-1 break-words font-medium tabular-nums text-foreground ${emphasis ? "text-xl sm:text-2xl" : "text-sm"}`}>
        {displayValue(value, kind)}
      </p>
    </div>
  );
}

function ResultHero({
  accent,
  eyebrow,
  value,
  valueKind = "money",
  detail,
  children,
}: {
  accent: HeroAccent;
  eyebrow: string;
  value: string | number | null;
  valueKind?: ValueKind;
  detail?: string | null;
  children?: ReactNode;
}) {
  return (
    <div className={`rounded-xl border border-border bg-card px-5 py-5 sm:px-6 sm:py-6 ${heroAccentEdge[accent]}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">{eyebrow}</p>
        {children}
      </div>
      <p className="mt-4 break-words text-3xl font-semibold tracking-[-0.035em] tabular-nums text-foreground sm:text-4xl lg:text-5xl">
        {displayValue(value, valueKind)}
      </p>
      {detail ? <p className="mt-2.5 text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}

export function PlanningStatusBadge({ status, neutral = false }: { status: string; neutral?: boolean }) {
  const style = neutral ? "border-border bg-muted/40 text-foreground" : statusBadgeStyles[status] ?? "border-border bg-muted/40 text-muted-foreground";
  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.08em] ${style}`}>
      {statusLabels[status] ?? status}
    </span>
  );
}

function sourceLabel(fact: InitialWealthFact) {
  if (fact.source === "INVESTMENT_PORTFOLIO_SNAPSHOT") return "MyProfit";
  if (fact.source === "GOAL_CURRENT_AMOUNT") return "Valor atual da meta";
  return "Informado por você";
}

function formatTimestamp(value: string | null) {
  if (!value) return null;
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(value);
  return match ? `${formatBRDate(match[1])} às ${match[2]}` : null;
}

function InitialWealthProvenance({ fact }: { fact: InitialWealthFact }) {
  const referenceMonth = fact.as_of.reference_month ?? fact.provenance.reference_month;
  const portfolio = fact.source === "INVESTMENT_PORTFOLIO_SNAPSHOT";
  const observedAt = portfolio ? null : formatTimestamp(fact.as_of.observed_at);
  const versionAt = portfolio ? formatTimestamp(fact.provenance.updated_at) : null;

  return (
    <details className="group mt-1 border-t border-border pt-3">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-[10px] text-muted-foreground marker:hidden">
        <span className="font-medium text-muted-foreground">
          {sourceLabel(fact)}
          {portfolio && referenceMonth ? ` · ${formatReferenceMonth(referenceMonth)}` : ""}
        </span>
        <span className="text-muted-foreground transition-colors hover:text-muted-foreground">Ver origem</span>
      </summary>
      <div className="mt-2 grid gap-1 pl-0 text-[10px] leading-5 text-muted-foreground">
        <p>Patrimônio inicial: <span className="font-medium text-foreground/90">{formatBRLDecimalString(fact.amount)}</span></p>
        {observedAt ? <p>Informado em: {observedAt}</p> : null}
        {versionAt ? <p>Versão importada em: {versionAt}</p> : null}
      </div>
    </details>
  );
}

// Metrics grid — editorial style with subtle dividers, no individual card borders
function MetricsGrid({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`grid divide-y divide-border rounded-xl border border-border bg-card px-4 sm:divide-y-0 sm:divide-x ${className}`}>
      {children}
    </div>
  );
}

export function ProjectionResult({ result }: { result: ForwardProjectionResponse }) {
  return (
    <section aria-live="polite" className="mt-8 space-y-5">
      <ResultHero
        accent="violet"
        eyebrow={`Patrimônio projetado em ${result.horizon_months} meses`}
        value={result.final_wealth}
        detail={`Data-base: ${formatBRDate(result.as_of_date)}`}
      />
      <MetricsGrid className="sm:grid-cols-2 xl:grid-cols-4 sm:px-0">
        <div className="sm:px-4"><Metric label="Patrimônio inicial" value={result.initial_wealth} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Aportes totais" value={result.total_contributions} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Crescimento projetado" value={result.total_projected_growth} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Taxa anual aplicada" value={result.effective_projection_annual_rate} kind="annualRate" /></div>
      </MetricsGrid>
      <div className="px-4">
        <Metric label="Taxa mensal equivalente" value={result.monthly_equivalent_rate} kind="monthlyRate" />
      </div>
      <InitialWealthProvenance fact={result.initial_wealth_fact} />
      <div className="mt-8">
        <ProjectionChart result={result} />
      </div>
    </section>
  );
}

export function TargetResult({ result }: { result: TargetAchievementResult }) {
  const isAchieved = result.status === "ACHIEVED" || result.status === "ALREADY_ACHIEVED";
  const accent: HeroAccent = isAchieved ? "emerald" : "amber";

  const detail = result.months_required !== null
    ? `${displayValue(result.months_required, "months")}${result.achievement_date ? ` · ${formatBRDate(result.achievement_date)}` : ""}`
    : statusLabels[result.status] ?? result.status;

  return (
    <section aria-live="polite" className="mt-8 space-y-5">
      <ResultHero accent={accent} eyebrow="Patrimônio-alvo" value={result.achieved_wealth ?? result.target_amount} detail={detail}>
        <PlanningStatusBadge status={result.status} />
      </ResultHero>
      <MetricsGrid className="sm:grid-cols-2 xl:grid-cols-4 sm:px-0">
        <div className="sm:px-4"><Metric label="Patrimônio-alvo" value={result.target_amount} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Patrimônio alcançado" value={result.achieved_wealth} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Prazo" value={result.months_required} kind="months" /></div>
        <div className="sm:px-4"><Metric label="Data de alcance" value={result.achievement_date} kind="date" /></div>
      </MetricsGrid>
      <InitialWealthProvenance fact={result.initial_wealth_fact} />
      {result.projection_result ? (
        <div className="mt-8">
          <ProjectionChart result={result.projection_result} targetAmount={result.target_amount} />
        </div>
      ) : null}
    </section>
  );
}

export function RequiredContributionResult({ result }: { result: RequiredContributionResponse }) {
  return (
    <section aria-live="polite" className="mt-8 space-y-5">
      <ResultHero accent="amber" eyebrow="Aporte mensal necessário" value={result.required_monthly_contribution} detail={statusLabels[result.status] ?? result.status}>
        <PlanningStatusBadge status={result.status} />
      </ResultHero>
      <MetricsGrid className="sm:grid-cols-2 xl:grid-cols-4 sm:px-0">
        <div className="sm:px-4"><Metric label="Patrimônio-alvo" value={result.target_amount} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Aporte informado" value={result.assumptions_template.scenario_monthly_contribution} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Prazo" value={result.target_achievement_result.months_required} kind="months" /></div>
        <div className="sm:px-4"><Metric label="Base do alvo" value={result.target_value_basis === "REAL" ? "Valores reais" : "Valores nominais"} /></div>
      </MetricsGrid>
      <InitialWealthProvenance fact={result.initial_wealth_fact} />
      {result.target_achievement_result.projection_result ? (
        <div className="mt-8">
          <ProjectionChart result={result.target_achievement_result.projection_result} targetAmount={result.target_amount} />
        </div>
      ) : null}
    </section>
  );
}

export function GoalPlanningResult({ result }: { result: GoalPlanningResponse }) {
  const isAchieved = result.status === "ALREADY_ACHIEVED" || result.status === "PROJECTED_EARLY" || result.status === "PROJECTED_ON_TIME";
  const accent: HeroAccent = isAchieved ? "emerald" : result.status === "PROJECTED_LATE" ? "amber" : "zinc";

  return (
    <section aria-live="polite" className="mt-8 space-y-5">
      <ResultHero accent={accent} eyebrow={result.goal_fact.name} value={statusLabels[result.status] ?? result.status} valueKind="text" detail={`Meta: ${formatBRLDecimalString(result.goal_fact.target_amount)}`}>
        <PlanningStatusBadge status={result.status} />
      </ResultHero>
      <MetricsGrid className="sm:grid-cols-2 xl:grid-cols-4 sm:px-0">
        <div className="sm:px-4"><Metric label="Meta" value={result.goal_fact.target_amount} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Valor atual da meta" value={result.goal_fact.current_amount} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Aporte planejado" value={result.goal_fact.goal_planned_monthly_contribution} kind="money" /></div>
        <div className="sm:px-4"><Metric label="Prazo da meta" value={result.goal_fact.target_date} kind="date" /></div>
      </MetricsGrid>
      {result.initial_wealth_fact ? <InitialWealthProvenance fact={result.initial_wealth_fact} /> : null}
      {result.target_achievement_result ? <TargetResult result={result.target_achievement_result} /> : null}
    </section>
  );
}

function ScenarioResultCard({ entry, referenceScenarioId, index }: { entry: ScenarioComparisonEntry; referenceScenarioId: string; index: number }) {
  const reference = entry.scenario_id === referenceScenarioId;
  const name = entry.label?.trim() || `Cenário ${index + 1}`;
  const accent = [
    { edge: "border-l-violet-400/55", icon: "bg-violet-400/10 text-violet-700 dark:text-violet-300", value: "text-violet-700 dark:text-violet-300" },
    { edge: "border-l-sky-400/55", icon: "bg-sky-400/10 text-sky-700 dark:text-sky-300", value: "text-sky-700 dark:text-sky-300" },
    { edge: "border-l-emerald-400/55", icon: "bg-emerald-400/10 text-success-foreground", value: "text-success-foreground" },
    { edge: "border-l-amber-400/55", icon: "bg-amber-400/10 text-warning-foreground", value: "text-warning-foreground" },
  ][index % 4]!;

  return (
    <article className={`min-w-0 space-y-4 rounded-xl border border-l-[3px] p-4 sm:p-5 ${reference
      ? "border-border border-l-zinc-400/45 bg-card"
      : `border-border bg-card ${accent.edge}`
    }`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${reference ? "bg-muted/45 text-muted-foreground" : accent.icon}`}><TrendingUp aria-hidden="true" size={15} /></span>
          <div className="min-w-0">
            <p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">{reference ? "Referência" : `Cenário ${index + 1}`}</p>
            <h4 className="mt-1 break-words text-base font-semibold leading-snug text-foreground [overflow-wrap:anywhere]">{name}</h4>
            {entry.archetype ? <p className="mt-0.5 text-xs text-muted-foreground">{entry.archetype === "CONSERVATIVE" ? "Conservador" : entry.archetype === "OPTIMISTIC" ? "Otimista" : "Base"}</p> : null}
          </div>
        </div>
        {entry.target_achievement_result ? <PlanningStatusBadge status={entry.target_achievement_result.status} /> : null}
      </div>

      {/* Projected wealth — hero metric within card */}
      <div className="border-t border-border pt-3">
        <p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">Patrimônio projetado</p>
        <p className={`mt-1 break-words text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl ${reference ? "text-foreground" : accent.value}`}>{displayValue(entry.projection_result.final_wealth, "money")}</p>
      </div>

      {/* Secondary metrics — typographic grid, no nested card borders */}
      <div className="grid grid-cols-2 divide-x divide-border border-t border-border pt-3">
        <div className="pr-4"><Metric label="Aportes totais" value={entry.projection_result.total_contributions} kind="money" /></div>
        <div className="pl-4"><Metric label="Crescimento projetado" value={entry.projection_result.total_projected_growth} kind="money" /></div>
      </div>

      {/* Delta metrics — higher contrast for the values, muted labels */}
      <div className="grid grid-cols-2 divide-x divide-border border-t border-border pt-3">
        <div className="pr-4">
          <p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">Diferença de patrimônio</p>
          <p className="mt-1 text-sm font-medium tabular-nums text-foreground">{displayValue(entry.final_wealth_delta, "money")}</p>
        </div>
        <div className="pl-4">
          <p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">Meses ganhos/perdidos</p>
          <p className="mt-1 text-sm font-medium tabular-nums text-foreground">
            {entry.months_saved_or_lost !== null && entry.months_saved_or_lost !== undefined
              ? displayValue(entry.months_saved_or_lost, "months")
              : "—"}
          </p>
        </div>
      </div>

      <InitialWealthProvenance fact={entry.initial_wealth_fact} />
    </article>
  );
}

export function ScenarioComparisonResult({ result }: { result: ScenarioComparisonResponse }) {
  return (
    <section aria-live="polite" className="mt-8 space-y-5">
      <ResultHero
        accent="sky"
        eyebrow="Comparação de cenários"
        value={`${result.entries.length} cenários analisados`}
        valueKind="text"
        detail={`Referência definida por você · ${result.horizon_months} meses`}
      ><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-400/10 text-sky-700 dark:text-sky-300"><GitCompareArrows aria-hidden="true" size={17} /></span></ResultHero>
      <div className="grid gap-4 xl:grid-cols-2">
        {result.entries.map((entry, index) => (
          <ScenarioResultCard key={entry.scenario_id} entry={entry} referenceScenarioId={result.reference_scenario_id} index={index} />
        ))}
      </div>
      <div className="mt-8">
        <ScenarioComparisonChart entries={result.entries} referenceScenarioId={result.reference_scenario_id} />
      </div>
    </section>
  );
}
