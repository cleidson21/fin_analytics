import type { ReactNode } from "react";

import type { FireAnalysisResponse, FireSummaryStatus } from "@/lib/fire";
import type { InitialWealthFact, RequiredContributionResponse, RequiredContributionStatus, TargetAchievementResponse, TargetAchievementStatus } from "@/lib/planning";
import { formatAnnualRateDecimalString, formatBRDate, formatBRLDecimalString, formatRateDecimalString, formatReferenceMonth } from "@/lib/planningLocale";

export type FireResultState = { result: FireAnalysisResponse | null; submittedSnapshot: string | null; pending: boolean; error: string | null };

export function createFireResultState(): FireResultState { return { result: null, submittedSnapshot: null, pending: false, error: null }; }
export function beginFireSubmission(state: FireResultState): FireResultState { return { ...state, pending: true, error: null }; }
export function completeFireSubmission(state: FireResultState, result: FireAnalysisResponse, submittedSnapshot: string): FireResultState { return { ...state, result, submittedSnapshot, pending: false, error: null }; }
export function failFireSubmission(state: FireResultState, error: string): FireResultState { return { ...state, pending: false, error }; }
export function isFireResultDirty(state: FireResultState, currentSnapshot: string): boolean { return state.result !== null && state.submittedSnapshot !== currentSnapshot; }
export function formatFireProgressRatio(value: string): string { return formatRateDecimalString(value, 2, ""); }

export function fireSummaryStatusCopy(status: FireSummaryStatus): string {
  return status === "ALREADY_FINANCIALLY_INDEPENDENT" ? "Meta alcançada pelas premissas informadas" : "Em construção";
}

export function projectedDateStatusCopy(status: TargetAchievementStatus): string {
  return {
    ALREADY_ACHIEVED: "Meta já alcançada na data-base.",
    ACHIEVED: "Meta alcançada no período projetado.",
    NOT_REACHED_WITHIN_HORIZON: "Meta não alcançada dentro do horizonte analisado.",
    UNREACHABLE: "Com estas premissas, a meta não é alcançada no cenário calculado.",
  }[status];
}

export function requiredContributionStatusCopy(status: RequiredContributionStatus): string {
  return {
    ALREADY_ACHIEVED: "Meta já alcançada na data-base.",
    ZERO_CONTRIBUTION_REQUIRED: "Nenhum aporte adicional é necessário pelas premissas informadas.",
    SOLVED: "Para a data e premissas informadas.",
    IMPOSSIBLE_HORIZON: "A data informada não permite calcular um aporte dentro do horizonte suportado.",
    OUT_OF_SUPPORTED_RANGE: "Com estas premissas, o aporte necessário fica fora do intervalo suportado.",
  }[status];
}

export type FireModeResult = { kind: "SUMMARY" } | { kind: "PROJECTED_DATE"; result: TargetAchievementResponse } | { kind: "REQUIRED_CONTRIBUTION"; result: RequiredContributionResponse };
export function selectFireModeResult(result: FireAnalysisResponse): FireModeResult {
  if (result.analysis_type === "PROJECTED_DATE" && result.projection) return { kind: "PROJECTED_DATE", result: result.projection };
  if (result.analysis_type === "REQUIRED_CONTRIBUTION" && result.required_contribution) return { kind: "REQUIRED_CONTRIBUTION", result: result.required_contribution };
  return { kind: "SUMMARY" };
}

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <div className="min-w-0 py-3 sm:px-4"><p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">{label}</p><p className="mt-1 break-words font-medium tabular-nums text-foreground">{value}</p>{detail ? <p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p> : null}</div>;
}

function MetricsGrid({ children }: { children: ReactNode }) {
  return <div className="grid divide-y divide-border rounded-xl border border-border bg-card px-4 sm:grid-cols-2 sm:divide-x sm:divide-y-0 sm:px-0 lg:grid-cols-4">{children}</div>;
}

function ResultHero({ result }: { result: FireAnalysisResponse }) {
  const achieved = result.summary.summary_status === "ALREADY_FINANCIALLY_INDEPENDENT";
  const className = ["rounded-xl border border-border bg-card px-5 py-5 sm:px-6 sm:py-6", achieved ? "border-l-2 border-l-emerald-400/40" : "border-l-2 border-l-violet-400/40"].join(" ");
  const badgeClass = ["inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.08em]", achieved ? "border-emerald-400/25 bg-emerald-400/10 text-success-foreground" : "border-amber-400/25 bg-amber-400/10 text-warning-foreground"].join(" ");
  return <section className={className}><div className="flex flex-wrap items-start justify-between gap-3"><p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">Meta de independência financeira</p><span className={badgeClass}>{fireSummaryStatusCopy(result.summary.summary_status)}</span></div><p className="mt-4 break-words text-3xl font-semibold tracking-[-0.035em] tabular-nums text-foreground sm:text-4xl lg:text-5xl">{formatBRLDecimalString(result.summary.fire_target)}</p><p className="mt-2.5 text-xs text-muted-foreground">Estimativa em valores reais, com base nas premissas informadas.</p></section>;
}

function SummaryMetrics({ result }: { result: FireAnalysisResponse }) {
  const achieved = result.summary.summary_status === "ALREADY_FINANCIALLY_INDEPENDENT";
  return <MetricsGrid><Metric label="Patrimônio elegível" value={formatBRLDecimalString(result.summary.eligible_investment_wealth)} /><Metric label="Progresso" value={formatFireProgressRatio(result.summary.progress_ratio)} /><Metric label={achieved ? "Situação da meta" : "Quanto falta"} value={achieved ? "Meta alcançada" : formatBRLDecimalString(result.summary.gap_to_fire)} detail={achieved ? "Valor restante: " + formatBRLDecimalString(result.summary.gap_to_fire) : undefined} /><Metric label="Capacidade mensal sob a taxa informada" value={formatBRLDecimalString(result.summary.supported_monthly_withdrawal)} detail={"Capacidade anual: " + formatBRLDecimalString(result.summary.supported_annual_withdrawal)} /></MetricsGrid>;
}

function ProjectedDateResult({ result }: { result: TargetAchievementResponse }) {
  const achieved = result.status === "ALREADY_ACHIEVED" || result.status === "ACHIEVED";
  const className = ["rounded-xl border p-5", achieved ? "border-emerald-400/20 bg-emerald-400/[0.045]" : "border-amber-400/20 bg-amber-400/[0.045]"].join(" ");
  return <section className={className}><p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">Quando atinjo?</p><p className="mt-2 break-words text-xl font-semibold tabular-nums text-foreground">{result.achievement_date ? formatBRDate(result.achievement_date) : projectedDateStatusCopy(result.status)}</p><p className="mt-2 text-sm leading-6 text-muted-foreground">{projectedDateStatusCopy(result.status)}</p></section>;
}

function RequiredContributionResult({ result }: { result: RequiredContributionResponse }) {
  const solved = result.status === "SOLVED";
  const className = ["rounded-xl border p-5", solved ? "border-violet-400/20 bg-violet-400/[0.045]" : "border-amber-400/20 bg-amber-400/[0.045]"].join(" ");
  return <section className={className}><p className="text-[10px] font-medium uppercase tracking-[0.13em] text-muted-foreground">{solved ? "Aporte mensal necessário" : "Resultado do aporte"}</p>{solved ? <p className="mt-2 break-words text-2xl font-semibold tabular-nums text-foreground">{formatBRLDecimalString(result.required_monthly_contribution)}</p> : null}<p className="mt-2 text-sm leading-6 text-muted-foreground">{requiredContributionStatusCopy(result.status)}</p></section>;
}

function Assumption({ label, value }: { label: string; value: string }) { return <div><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 font-medium tabular-nums text-foreground">{value}</dd></div>; }
function Assumptions({ result }: { result: FireAnalysisResponse }) {
  const item = result.assumptions;
  return <details className="rounded-xl border border-border bg-muted/25 p-4"><summary className="cursor-pointer text-sm font-semibold text-foreground">Premissas utilizadas</summary><dl className="mt-4 grid gap-x-6 gap-y-3 border-t border-border pt-4 text-sm sm:grid-cols-2"><Assumption label="Gasto mensal desejado" value={formatBRLDecimalString(item.monthly_retirement_spending)} /><Assumption label="Taxa anual de retirada assumida" value={formatAnnualRateDecimalString(item.assumed_annual_withdrawal_rate)} />{item.scenario_monthly_contribution !== null ? <Assumption label="Aporte do cenário" value={formatBRLDecimalString(item.scenario_monthly_contribution)} /> : null}{item.expected_return_rate !== null ? <Assumption label="Retorno anual esperado" value={formatAnnualRateDecimalString(item.expected_return_rate)} /> : null}{item.return_type !== null ? <Assumption label="Tipo do retorno" value={item.return_type === "REAL" ? "Real" : "Nominal"} /> : null}{item.inflation_rate !== null ? <Assumption label="Inflação anual" value={formatAnnualRateDecimalString(item.inflation_rate)} /> : null}{item.horizon_months !== null ? <Assumption label="Horizonte" value={String(item.horizon_months) + (item.horizon_months === 1 ? " mês" : " meses")} /> : null}{item.desired_fire_date !== null ? <Assumption label="Data desejada" value={formatBRDate(item.desired_fire_date)} /> : null}</dl></details>;
}

function observedAt(value: string | null): string | null {
  if (!value) return null;
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(value);
  return match ? formatBRDate(match[1]) + " às " + match[2] : null;
}
function Provenance({ fact, asOfDate }: { fact: InitialWealthFact; asOfDate: string }) {
  const portfolio = fact.source === "INVESTMENT_PORTFOLIO_SNAPSHOT";
  const referenceMonth = fact.as_of.reference_month ?? fact.provenance.reference_month;
  const timestamp = observedAt(fact.as_of.observed_at);
  return <details className="border-t border-border pt-4 text-xs leading-5 text-muted-foreground"><summary className="cursor-pointer font-medium text-foreground/90">Fonte e data-base</summary><div className="mt-2 grid gap-1 sm:grid-cols-2 sm:gap-x-6"><p>{portfolio ? "Carteira de investimentos utilizada nesta análise." : "Valor informado por você."}</p><p>Data-base da análise: {formatBRDate(asOfDate)}</p>{portfolio && referenceMonth ? <p>Mês de referência: {formatReferenceMonth(referenceMonth)}</p> : null}{!portfolio && timestamp ? <p>Observado em: {timestamp}</p> : null}</div></details>;
}

export function FireResults({ result }: { result: FireAnalysisResponse }) {
  const modeResult = selectFireModeResult(result);
  return <div className="space-y-5"><ResultHero result={result} /><SummaryMetrics result={result} />{modeResult.kind === "PROJECTED_DATE" ? <ProjectedDateResult result={modeResult.result} /> : null}{modeResult.kind === "REQUIRED_CONTRIBUTION" ? <RequiredContributionResult result={modeResult.result} /> : null}<Assumptions result={result} /><Provenance fact={result.provenance.initial_wealth_fact} asOfDate={result.as_of_date} /></div>;
}

function ResultSkeleton() { return <div aria-hidden="true" className="space-y-4 rounded-xl border border-border bg-card p-5 motion-safe:animate-pulse motion-reduce:animate-none"><div className="h-3 w-44 rounded bg-muted/60" /><div className="h-11 w-3/5 rounded bg-muted/70" /><div className="grid gap-3 sm:grid-cols-2"><div className="h-16 rounded bg-muted/50" /><div className="h-16 rounded bg-muted/50" /></div></div>; }
export function FireResultRegion({ state, currentSnapshot, action }: { state: FireResultState; currentSnapshot: string; action?: ReactNode }) {
  const dirty = isFireResultDirty(state, currentSnapshot);
  if (!state.result && state.pending) return <section className="mt-8" aria-label="Resultado da análise"><p role="status" className="sr-only">Calculando análise…</p><ResultSkeleton /></section>;
  if (!state.result && state.error) return <section className="mt-6" aria-label="Resultado da análise"><p role="alert" className="rounded-xl border border-rose-400/20 bg-rose-400/[0.055] p-4 text-sm text-destructive">{state.error}</p></section>;
  if (!state.result) return null;
  return <section className="mt-8" aria-label="Resultado da análise">{state.pending ? <p role="status" className="mb-3 text-xs text-muted-foreground">Atualizando análise…</p> : null}{!state.pending && dirty ? <p className="mb-3 text-xs text-muted-foreground">Premissas alteradas · analise novamente.</p> : null}{state.error ? <p role="alert" className="mb-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.055] p-4 text-sm text-destructive">{state.error} O resultado exibido é da análise anterior.</p> : null}<div className={["transition-[opacity,transform] duration-200 ease-out motion-reduce:transform-none motion-reduce:transition-none", state.pending || dirty ? "opacity-60" : "opacity-100"].join(" ")}><FireResults result={state.result} /></div>{!state.pending && !dirty && !state.error && action ? <div className="mt-5 flex justify-end border-t border-border pt-5">{action}</div> : null}</section>;
}
