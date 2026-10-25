"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { type ChangeEvent, useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Bot,
  CheckCircle2,
  CircleDollarSign,
  Database,
  Flag,
  Layers3,
  LoaderCircle,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  WalletCards,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { buildHrefWithSearchParams } from "@/config/navigation";
import { formatBRLDecimalString, formatReferenceMonth } from "@/lib/planningLocale";
import {
  getCurrentReferenceMonth,
  loadWealthHome,
  resolveReferenceMonth,
  type WealthHomeAvailability,
  type WealthHomeReadModel,
  type WealthHomeSourceReadModel,
} from "@/lib/wealthHome";

import { SYNTHETIC_WEALTH_HOME_FIXTURE as fixture } from "../fixtures";
import { useTransientAnalysis } from "../TransientAnalysisContext";
import type { TransientAnalysisSelection } from "../transientAnalysis";
import type {
  WealthHomeMetric,
  WealthHomeMetricTone,
  WealthHomePreviewState,
} from "../types";
import { TransientAnalysisPanel } from "./TransientAnalysisPanel";

const STATE_OPTIONS: ReadonlyArray<{
  id: WealthHomePreviewState;
  label: string;
}> = [
  { id: "success", label: "Sucesso" },
  { id: "loading", label: "Carregando" },
  { id: "empty", label: "Sem dados" },
  { id: "error", label: "Erro" },
];

const METRIC_STYLES: Record<WealthHomeMetricTone, string> = {
  emerald: "border-emerald-400/20 bg-emerald-400/[0.07] text-success-foreground",
  sky: "border-sky-400/20 bg-sky-400/[0.07] text-sky-700 dark:text-sky-300",
  violet: "border-violet-400/20 bg-violet-400/[0.07] text-violet-700 dark:text-violet-300",
  amber: "border-amber-400/20 bg-amber-400/[0.07] text-warning-foreground",
};

type WealthHomeMode = "authenticated" | "demo";
type AuthenticatedLoadState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "success"; data: WealthHomeReadModel };

function SourceBadge({ mode }: { mode: WealthHomeMode }) {
  const authenticated = mode === "authenticated";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.13em]",
        authenticated
          ? "border-emerald-300/25 bg-emerald-300/10 text-success-foreground"
          : "border-amber-300/25 bg-amber-300/10 text-warning-foreground",
      )}
    >
      <Database className="h-3.5 w-3.5" aria-hidden="true" />
      {authenticated ? "Dados governados" : "Modo demonstrativo"}
    </span>
  );
}

function ModeSelector({
  value,
  onChange,
}: {
  value: WealthHomeMode;
  onChange: (mode: WealthHomeMode) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="sr-only">
        Origem dos cartões
      </span>
      <div className="flex rounded-xl border border-border bg-muted/35 p-1">
        <button
          type="button"
          aria-pressed={value === "authenticated"}
          onClick={() => onChange("authenticated")}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
            value === "authenticated"
              ? "bg-emerald-400/15 text-success-foreground"
              : "text-muted-foreground hover:text-foreground/90",
          )}
        >
          Dados autenticados
        </button>
        <button
          type="button"
          aria-pressed={value === "demo"}
          onClick={() => onChange("demo")}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
            value === "demo"
              ? "bg-amber-400/15 text-warning-foreground"
              : "text-muted-foreground hover:text-foreground/90",
          )}
        >
          Demonstração
        </button>
      </div>
    </div>
  );
}

function PreviewStateSelector({
  value,
  onChange,
}: {
  value: WealthHomePreviewState;
  onChange: (next: WealthHomePreviewState) => void;
}) {
  return (
    <div className="flex flex-col gap-2 sm:items-end">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
        Prévia dos estados da interface
      </span>
      <div className="flex flex-wrap gap-1 rounded-2xl border border-border bg-muted/35 p-1">
        {STATE_OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            aria-pressed={value === option.id}
            onClick={() => onChange(option.id)}
            className={cn(
              "rounded-xl px-3 py-2 text-xs font-semibold transition-colors",
              value === option.id
                ? "bg-muted/70 text-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted/40 hover:text-foreground/90",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function MonthSelector({
  value,
  maximum,
  onChange,
}: {
  value: string;
  maximum: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <label className="flex w-full items-center gap-2 sm:w-auto">
      <span className="whitespace-nowrap text-xs font-medium text-muted-foreground">Mês</span>
      <input
        aria-label="Mês de referência da Wealth Home"
        type="month"
        value={value}
        max={maximum}
        onChange={onChange}
        className="min-h-9 w-full rounded-xl border border-border bg-muted/45 px-3 py-1.5 text-sm font-semibold text-foreground outline-none transition focus:border-emerald-300/50 focus:ring-2 focus:ring-emerald-300/15 sm:w-44"
      />
    </label>
  );
}

function LoadingState({ authenticated = false }: { authenticated?: boolean }) {
  return (
    <section
      aria-label="Carregando visão geral"
      className="grid animate-pulse gap-4 md:grid-cols-2 xl:grid-cols-4"
    >
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="min-h-44 rounded-2xl border border-border bg-muted/30 p-4"
        >
          <div className="mb-7 h-3 w-24 rounded-full bg-muted/55" />
          <div className="mb-4 h-8 w-36 rounded-xl bg-muted/65" />
          <div className="h-3 w-full rounded-full bg-muted/45" />
        </div>
      ))}
      <div className="col-span-full flex items-center justify-center gap-2 py-4 text-sm text-muted-foreground">
        <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
        {authenticated ? "Lendo dados governados com escopo autenticado…" : "Preparando o panorama demonstrativo…"}
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="rounded-2xl border border-dashed border-border bg-muted/30 px-5 py-8 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-muted/45 text-muted-foreground">
        <WalletCards className="h-6 w-6" aria-hidden="true" />
      </div>
      <h2 className="text-base font-semibold text-foreground">Ainda não há dados para compor esta visão</h2>
      <p className="mx-auto mt-2 max-w-xl text-xs leading-5 text-muted-foreground">A ausência foi preservada; nenhum valor foi fabricado.</p>
      <div className="mt-4 flex flex-wrap justify-center gap-3">
        <Link
          href="/governance/imports"
          className="rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring"
        >
          Revisar importações
        </Link>
        <Link
          href="/wealth-intelligence/health"
          className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-muted/45"
        >
          Abrir Saúde Financeira
        </Link>
      </div>
    </section>
  );
}

function ErrorState({
  onRetry,
  authenticated = true,
}: {
  onRetry: () => void;
  authenticated?: boolean;
}) {
  return (
    <section
      role="alert"
      className="rounded-2xl border border-red-400/20 bg-red-400/[0.05] px-5 py-8 text-center"
    >
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-red-400/10 text-red-300">
        <AlertTriangle className="h-6 w-6" aria-hidden="true" />
      </div>
      <h2 className="text-base font-semibold text-foreground">Não foi possível carregar a visão geral</h2>
      <p className="mx-auto mt-2 max-w-xl text-xs leading-5 text-muted-foreground">
        {authenticated
          ? "Health, Goals e Investments estão indisponíveis; nenhuma fixture foi usada como substituta."
          : "Erro demonstrativo; nenhuma chamada de rede ou dado pessoal foi utilizado."}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring"
      >
        <RefreshCw className="h-4 w-4" aria-hidden="true" />
        Tentar novamente
      </button>
    </section>
  );
}

const FRESHNESS_LABELS: Record<WealthHomeSourceReadModel["freshness"], string> = {
  CURRENT: "estado atual",
  PARTIAL_PERIOD: "período em aberto",
  CLOSED_PERIOD: "período encerrado",
  UNKNOWN: "frescor desconhecido",
};

const COMPLETENESS_LABELS: Record<WealthHomeSourceReadModel["completeness"], string> = {
  COMPLETE: "completo",
  PARTIAL: "parcial",
  UNKNOWN: "completude não certificada",
};

const AVAILABILITY_LABELS: Record<WealthHomeAvailability, string> = {
  AVAILABLE: "disponível",
  UNAVAILABLE: "indisponível",
  INSUFFICIENT_DATA: "sem dado suficiente",
};

function goalCount(data: WealthHomeReadModel, status: string): number {
  return data.goals.by_status.find((item) => item.status === status)?.count ?? 0;
}

function formatTechnicalTimestamp(value: string | null): string {
  if (value === null) return "não informado";
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:\d{2})?$/.exec(value);
  if (!match) return value;
  const [, year, month, day, hour, minute, zone] = match;
  const zoneLabel = zone === "Z" ? "UTC" : zone ? `UTC${zone}` : "fuso não informado";
  return `${day}/${month}/${year} às ${hour}:${minute} · ${zoneLabel}`;
}

function SourceDetails({
  source,
  availability,
}: {
  source: WealthHomeSourceReadModel;
  availability: WealthHomeAvailability | null;
}) {
  return (
    <details className="group mt-2 text-[11px] text-muted-foreground">
      <summary className="cursor-pointer list-none font-medium text-muted-foreground marker:hidden hover:text-foreground">
        Fonte e qualidade
      </summary>
      <dl className="mt-2 grid gap-1.5 rounded-xl border border-border bg-muted/30 p-3">
        {availability ? (
          <div className="flex justify-between gap-3">
            <dt>Estado</dt>
            <dd className="text-right text-foreground/90">{AVAILABILITY_LABELS[availability]}</dd>
          </div>
        ) : null}
        <div className="flex justify-between gap-3">
          <dt>Completude</dt>
          <dd className="text-right text-foreground/90">{COMPLETENESS_LABELS[source.completeness]}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Reader</dt>
          <dd className="break-all text-right text-foreground/90">{source.reader} v{source.version}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Escopo</dt>
          <dd className="break-all text-right text-foreground/90">{source.scope}</dd>
        </div>
      </dl>
    </details>
  );
}

function InvestmentProvenanceDialog({ data }: { data: WealthHomeReadModel["investments"] }) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const usesEarlierSnapshot =
    data.snapshot_reference_month !== null &&
    data.snapshot_reference_month < data.requested_reference_month;

  const close = useCallback(() => {
    setOpen(false);
    window.requestAnimationFrame(() => triggerRef.current?.focus());
  }, []);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
      if (event.key === "Tab") {
        const focusable = Array.from(
          dialogRef.current?.querySelectorAll<HTMLElement>(
            "button:not([disabled]), summary, [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])",
          ) ?? [],
        );
        const first = focusable[0];
        const last = focusable.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [close, open]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen(true)}
        className="mt-3 rounded-lg border border-sky-300/15 bg-sky-300/[0.05] px-2.5 py-1.5 text-[11px] font-semibold text-sky-700 dark:text-sky-300 hover:bg-sky-300/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/40"
      >
        Detalhes de proveniência
      </button>
      {open && typeof document !== "undefined"
        ? createPortal(
          <div
            className="fixed inset-0 z-[80] flex items-stretch justify-end bg-black/70 p-0 backdrop-blur-sm sm:p-4"
            onMouseDown={(event) => {
              if (event.currentTarget === event.target) close();
            }}
          >
            <section
              ref={dialogRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              className="h-full w-full overflow-y-auto border-l border-border bg-background p-5 shadow-2xl sm:max-w-lg sm:rounded-3xl sm:border"
            >
              <div className="flex items-start justify-between gap-4 border-b border-border pb-4">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-sky-700 dark:text-sky-300">Investimentos governados</p>
                  <h2 id={titleId} className="mt-1 text-lg font-semibold text-foreground">Proveniência de Investments</h2>
                </div>
                <button
                  ref={closeRef}
                  type="button"
                  onClick={close}
                  aria-label="Fechar detalhes de proveniência"
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border text-muted-foreground hover:bg-muted/45 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/50"
                >
                  <X aria-hidden="true" size={17} />
                </button>
              </div>
              <section aria-labelledby={`${titleId}-summary`} className="mt-5 rounded-2xl border border-border bg-muted/30 p-4">
                <h3 id={`${titleId}-summary`} className="text-xs font-semibold uppercase tracking-[0.13em] text-muted-foreground">Resumo</h3>
                <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                  <div><dt className="text-xs text-muted-foreground">Fonte</dt><dd className="mt-1 text-foreground">{data.source_type ?? "não elegível"}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">Período</dt><dd className={cn("mt-1 font-medium", usesEarlierSnapshot ? "text-warning-foreground" : "text-foreground")}>{data.snapshot_reference_month ? formatReferenceMonth(data.snapshot_reference_month) : "não disponível"}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">Frescor</dt><dd className="mt-1 text-foreground">{FRESHNESS_LABELS[data.source.freshness]}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">Completude</dt><dd className="mt-1 text-foreground">{COMPLETENESS_LABELS[data.source.completeness]}</dd></div>
                </dl>
                <p className="mt-3 border-t border-border pt-3 text-xs leading-5 text-muted-foreground">
                  Patrimônio de investimentos; não representa patrimônio líquido total nem avaliação em tempo real.
                </p>
              </section>
              {usesEarlierSnapshot ? (
                <p className="mt-3 rounded-xl border border-amber-300/15 bg-amber-300/[0.06] px-3 py-2 text-xs leading-5 text-warning-foreground">
                  Snapshot anterior ao mês solicitado ({formatReferenceMonth(data.requested_reference_month)}).
                </p>
              ) : null}
              <details className="group mt-4 rounded-2xl border border-border bg-muted/30">
                <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-foreground/90 marker:hidden">Detalhes técnicos</summary>
                <dl className="grid gap-4 border-t border-border p-4 text-xs sm:grid-cols-2">
                  <div><dt className="text-muted-foreground">Run ID</dt><dd className="mt-1 break-all text-foreground/90">{data.run_id ?? "não disponível"}</dd></div>
                  <div><dt className="text-muted-foreground">Escopo do portfólio</dt><dd className="mt-1 break-all text-foreground/90">{data.portfolio_scope ?? "não disponível"}</dd></div>
                  <div><dt className="text-muted-foreground">Reader</dt><dd className="mt-1 break-all text-foreground/90">{data.source.reader} v{data.source.version}</dd></div>
                  <div><dt className="text-muted-foreground">Autoridade</dt><dd className="mt-1 break-all text-foreground/90">{data.source.authority}</dd></div>
                  <div><dt className="text-muted-foreground">Escopo de leitura</dt><dd className="mt-1 break-all text-foreground/90">{data.source.scope}</dd></div>
                  <div><dt className="text-muted-foreground">Mês solicitado</dt><dd className="mt-1 text-foreground/90">{formatReferenceMonth(data.requested_reference_month)}</dd></div>
                  <div><dt className="text-muted-foreground">Leitura</dt><dd className="mt-1 text-foreground/90">{formatTechnicalTimestamp(data.source.read_at)}</dd></div>
                  <div><dt className="text-muted-foreground">Atualização técnica</dt><dd className="mt-1 text-foreground/90">{formatTechnicalTimestamp(data.source.updated_at)}</dd></div>
                </dl>
              </details>
            </section>
          </div>,
          document.body,
        )
        : null}
    </>
  );
}

function OverviewMetrics({
  mode,
  data,
  healthHref,
  selection,
}: {
  mode: WealthHomeMode;
  data?: WealthHomeReadModel;
  healthHref: string;
  selection: TransientAnalysisSelection | null;
}) {
  const icons = [CircleDollarSign, WalletCards, Target, Flag] as const;
  const authenticated = mode === "authenticated" && data !== undefined;
  const metrics: Array<
    WealthHomeMetric & {
      origin: "governed" | "demo" | "on-demand";
      sourceMetadata: WealthHomeSourceReadModel | null;
      availability: WealthHomeAvailability | null;
    }
  > = fixture.metrics.map((metric) => ({
    ...metric,
    source: "Fixture sintética",
    origin: "demo" as const,
    sourceMetadata: null,
    availability: null,
  }));

  if (authenticated) {
    const healthAvailable =
      data.health.status === "AVAILABLE" && data.health.net_cashflow !== null;
    metrics[0] = {
      ...metrics[0],
      value: healthAvailable
        ? formatBRLDecimalString(data.health.net_cashflow!)
        : "Sem dado certificado",
      context: healthAvailable
        ? `Receitas menos despesas em ${formatReferenceMonth(data.health.reference_month)}`
        : "O backend não encontrou fato suficiente para este período",
      source: "Financial Health",
      origin: "governed",
      sourceMetadata: data.health.source,
      availability: data.health.status,
    };
    const investmentAvailable =
      data.investments.status === "AVAILABLE" &&
      data.investments.investment_wealth !== null &&
      data.investments.snapshot_reference_month !== null;
    const requestedInvestmentMonth = formatReferenceMonth(
      data.investments.requested_reference_month,
    );
    const snapshotInvestmentMonth = data.investments.snapshot_reference_month
      ? formatReferenceMonth(data.investments.snapshot_reference_month)
      : null;
    metrics[1] = {
      ...metrics[1],
      label: "Patrimônio de investimentos",
      value: investmentAvailable
        ? formatBRLDecimalString(data.investments.investment_wealth!)
        : "Sem dado governado",
      context: investmentAvailable
        ? snapshotInvestmentMonth === requestedInvestmentMonth
          ? `Snapshot de ${snapshotInvestmentMonth} · patrimônio de investimentos, não patrimônio líquido total`
          : `Último snapshot elegível: ${snapshotInvestmentMonth} · solicitado: ${requestedInvestmentMonth} · não é patrimônio líquido total`
        : `Nenhum snapshot MyProfit elegível para ${requestedInvestmentMonth} · não é patrimônio líquido total`,
      source: data.investments.source_type ?? "Investments",
      origin: "governed",
      sourceMetadata: data.investments.source,
      availability: data.investments.status,
    };
    metrics[2] = {
      ...metrics[2],
      label: "Metas autenticadas",
      value: String(data.goals.total_count),
      context:
        data.goals.total_count === 0
          ? "Fotografia atual: nenhuma meta autenticada cadastrada"
          : `Fotografia atual · ${goalCount(data, "ACTIVE")} ativas · ${goalCount(data, "ACHIEVED")} concluídas · ${goalCount(data, "PAUSED")} pausadas`,
      source: "Goals",
      origin: "governed",
      sourceMetadata: data.goals.source,
      availability: data.goals.status,
    };
    metrics[3] = {
      ...metrics[3],
      label: "Independência financeira",
      value: selection?.domain === "FIRE" ? "Análise selecionada" : "Nenhuma análise",
      context: selection?.domain === "FIRE"
        ? "Resultado transitório exibido abaixo com suas próprias premissas"
        : "Abra FIRE para executar uma análise determinística sob demanda",
      source: selection?.domain === "FIRE" ? "Selecionada pelo usuário" : "Sob demanda",
      origin: "on-demand",
      sourceMetadata: null,
      availability: null,
    };
  }

  const reference = authenticated
    ? formatReferenceMonth(data.reference_month)
    : fixture.referencePeriod;

  return (
    <section aria-labelledby="overview-title">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 id="overview-title" className="text-sm font-semibold text-foreground">Indicadores</h2>
        <span className="text-[11px] text-muted-foreground">Health e Investments: {reference} · Goals: atual</span>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric, index) => {
          const Icon = icons[index];
          return (
            <article key={metric.id} className="group flex min-h-52 flex-col rounded-2xl border border-border bg-muted/30 p-4 transition duration-200 hover:border-border hover:bg-muted/40">
              <div className="mb-4 flex items-start justify-between gap-3">
                <span
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-xl border",
                    METRIC_STYLES[metric.tone],
                  )}
                >
                  <Icon className="h-4.5 w-4.5" aria-hidden="true" />
                </span>
                <span
                  className={cn(
                    "rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider",
                    metric.origin === "governed"
                      ? "bg-emerald-400/10 text-success-foreground"
                      : metric.origin === "on-demand"
                        ? "bg-violet-400/10 text-violet-700 dark:text-violet-300"
                        : "bg-amber-400/10 text-warning-foreground",
                  )}
                >
                  {metric.origin === "governed"
                    ? "Governado"
                    : metric.origin === "on-demand"
                      ? "Sob demanda"
                      : "Demonstração"}
                </span>
              </div>
              <p className="text-xs font-medium text-muted-foreground">{metric.label}</p>
              <p className="mt-1.5 text-2xl font-semibold tracking-tight text-foreground">{metric.value}</p>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">{metric.context}</p>
              <div className="mt-auto border-t border-border pt-3">
                <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                  <span className="font-semibold uppercase tracking-[0.1em] text-muted-foreground">{metric.source}</span>
                  {metric.sourceMetadata ? <span className="rounded-full bg-muted/40 px-2 py-0.5 text-muted-foreground">{FRESHNESS_LABELS[metric.sourceMetadata.freshness]}</span> : null}
                </div>
                {index === 1 && authenticated ? (
                  <InvestmentProvenanceDialog data={data.investments} />
                ) : metric.sourceMetadata ? <SourceDetails source={metric.sourceMetadata} availability={metric.availability} /> : null}
                {index === 0 ? (
                  <Link href={healthHref} aria-label={`Abrir detalhamento de Saúde Financeira para ${reference}`} className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-sky-700 dark:text-sky-300 hover:text-foreground">Ver detalhes <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" /></Link>
                ) : null}
                {index === 2 ? (
                  <Link href="/wealth-intelligence/goals" className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-violet-700 dark:text-violet-300 hover:text-foreground">Abrir Metas <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" /></Link>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function PlanningAndFireEntryPoints({ selection }: { selection: TransientAnalysisSelection | null }) {
  const items = [
    {
      title: "Planejamento",
      status: selection?.domain === "PLANNING" ? "Análise selecionada na Visão Geral" : "Nenhum cenário selecionado",
      href: "/wealth-intelligence/planning?intent=simulate&from=wealth-home",
      action: "Abrir Planejamento",
      icon: BarChart3,
      tone: "text-violet-700 dark:text-violet-300 bg-violet-400/10 border-violet-300/15",
    },
    {
      title: "Independência Financeira",
      status: selection?.domain === "FIRE" ? "Análise selecionada na Visão Geral" : "Nenhuma análise executada",
      href: "/wealth-intelligence/fire?from=wealth-home",
      action: "Abrir FIRE",
      icon: Flag,
      tone: "text-warning-foreground bg-amber-400/10 border-amber-300/15",
    },
  ] as const;

  return (
    <section aria-labelledby="planning-fire-title">
      <h2 id="planning-fire-title" className="mb-3 text-sm font-semibold text-foreground">Análises sob demanda</h2>
      <div className="grid gap-3 lg:grid-cols-2">
        {items.map((item) => (
          <article key={item.href} className="rounded-2xl border border-border bg-muted/30 p-4">
            <div className="flex items-center gap-3">
              <span className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border", item.tone)}>
                <item.icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-foreground">{item.title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{item.status}</p>
              </div>
              <Link href={item.href} aria-label={item.action} className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border text-muted-foreground hover:bg-muted/45 hover:text-foreground"><ArrowRight className="h-4 w-4" aria-hidden="true" /></Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function InvestmentWealthChart() {
  return (
    <article className="rounded-[2rem] border border-border bg-muted/30 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700 dark:text-sky-300">
            Evolução observada
          </p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">Carteira de investimentos</h2>
          <p className="mt-1 text-xs text-muted-foreground">Histórico sintético · não representa performance</p>
        </div>
        <div className="text-right">
          <p className="text-xl font-semibold text-foreground">R$ 842.450,00</p>
          <p className="text-xs text-muted-foreground">snapshot de set/2026</p>
        </div>
      </div>

      <div className="mt-8 grid h-52 grid-cols-6 items-end gap-2 sm:gap-4" aria-label="Evolução sintética da carteira de abril a setembro">
        {fixture.investmentWealthHistory.map((point, index) => (
          <div key={point.period} className="flex h-full min-w-0 flex-col items-center justify-end gap-2">
            <span className="hidden text-[10px] font-medium text-muted-foreground sm:block">{point.value}</span>
            <div className="flex h-36 w-full items-end rounded-2xl bg-muted/30 p-1">
              <div
                className={cn(
                  "w-full rounded-xl bg-gradient-to-t transition-all duration-300",
                  index === fixture.investmentWealthHistory.length - 1
                    ? "from-emerald-500/45 to-emerald-300"
                    : "from-sky-500/15 to-sky-300/55",
                )}
                style={{ height: point.visualHeight }}
                title={`${point.period}: ${point.value}`}
              />
            </div>
            <span className="text-xs font-medium text-muted-foreground">{point.period}</span>
          </div>
        ))}
      </div>
      <p className="mt-5 flex items-start gap-2 rounded-2xl bg-sky-400/[0.05] px-4 py-3 text-xs leading-5 text-sky-700 dark:text-sky-300">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-sky-700 dark:text-sky-300" aria-hidden="true" />
        O contrato futuro deve preservar conta, período de referência, data de atualização e completude.
        Esta visualização usa somente alturas prontas da fixture.
      </p>
    </article>
  );
}

function GovernedInvestmentVisualizationsUnavailable() {
  return (
    <details className="group rounded-2xl border border-sky-400/15 bg-sky-400/[0.035]">
      <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3 marker:hidden">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sky-300/10 text-sky-700 dark:text-sky-300"><BarChart3 className="h-4 w-4" aria-hidden="true" /></span>
        <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-foreground">Evolução e alocação indisponíveis</span><span className="block text-xs text-muted-foreground">Sem série certificada para o modo autenticado</span></span>
        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-1 text-[9px] font-bold uppercase tracking-[0.12em] text-warning-foreground">Indisponível</span>
      </summary>
      <p className="border-t border-border px-4 py-3 text-xs leading-5 text-muted-foreground">
        O contrato atual certifica apenas o snapshot mensal. Evolução, alocação, concentração e performance continuam bloqueadas; os gráficos sintéticos aparecem somente em Demonstração.
      </p>
    </details>
  );
}

function AllocationView() {
  return (
    <article className="rounded-[2rem] border border-border bg-muted/30 p-5 sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-700 dark:text-violet-300">
            Composição
          </p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">Alocação demonstrativa</h2>
          <p className="mt-1 text-xs text-muted-foreground">Percentuais fornecidos pela fixture</p>
        </div>
        <Layers3 className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
      </div>

      <div className="mt-8 space-y-6">
        {fixture.allocation.map((item) => (
          <div key={item.label}>
            <div className="mb-2 flex items-end justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{item.value}</p>
              </div>
              <span className="text-sm font-semibold text-foreground">{item.share}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted/45">
              <div
                className="h-full rounded-full"
                style={{ width: item.visualWidth, backgroundColor: item.color }}
              />
            </div>
          </div>
        ))}
      </div>

      <Link
        href="/wealth"
        className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-violet-700 transition hover:text-violet-600 dark:text-violet-300 dark:hover:text-violet-200"
      >
        Abrir área operacional de investimentos
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </Link>
    </article>
  );
}

function AdvisorPreview() {
  return (
    <details className="group overflow-hidden rounded-2xl border border-violet-400/15 bg-violet-500/[0.035]">
      <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3 marker:hidden">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-300/10 text-violet-700 dark:text-violet-300"><Sparkles className="h-4 w-4" aria-hidden="true" /></span>
        <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-foreground">Advisor experimental</span><span className="block text-xs text-muted-foreground">Prévia sintética, sem modelo conectado</span></span>
        <span className="rounded-full border border-border bg-card px-2 py-1 text-[9px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Inferência desativada</span>
      </summary>
      <section aria-labelledby="advisor-title" className="grid gap-4 border-t border-border p-4 lg:grid-cols-2">
        <div>
          <h2 id="advisor-title" className="sr-only">Detalhes do Advisor</h2>
          <p className="text-[10px] font-bold uppercase tracking-[0.13em] text-muted-foreground">Pergunta sintética</p>
          <p className="mt-2 rounded-xl bg-muted/35 p-3 text-sm text-foreground">“{fixture.advisor.question}”</p>
          <div className="mt-3 space-y-2">{fixture.advisor.context.map((item) => <div key={item.label} className="rounded-xl bg-muted/30 p-3"><div className="flex justify-between gap-2"><p className="text-xs font-semibold text-foreground">{item.label}</p><span className="text-[9px] font-bold uppercase text-warning-foreground">Sintético</span></div><p className="mt-1 text-xs text-muted-foreground">{item.value}</p><p className="mt-1 text-[10px] text-muted-foreground">{item.provenance}</p></div>)}</div>
        </div>
        <div>
          <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.13em] text-muted-foreground"><LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />Resposta fixture</p>
          <div className="mt-2 flex gap-3 rounded-xl border border-violet-300/15 bg-muted/35 p-4"><Bot className="mt-0.5 h-4 w-4 shrink-0 text-violet-700 dark:text-violet-300" aria-hidden="true" /><p className="text-xs leading-6 text-foreground/90">{fixture.advisor.response}</p></div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2"><div><p className="text-[10px] font-bold uppercase text-muted-foreground">Fontes</p><ul className="mt-2 space-y-1">{fixture.advisor.sources.map((source) => <li key={source} className="flex gap-2 text-xs text-muted-foreground"><Database className="mt-0.5 h-3 w-3 shrink-0 text-sky-700 dark:text-sky-300" aria-hidden="true" />{source}</li>)}</ul></div><div><p className="text-[10px] font-bold uppercase text-muted-foreground">Limites</p><ul className="mt-2 space-y-1">{fixture.advisor.limitations.map((limitation) => <li key={limitation} className="flex gap-2 text-xs text-muted-foreground"><CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />{limitation}</li>)}</ul></div></div>
          <button type="button" disabled title="A ativação depende de auditoria durável e gateway de validação" className="mt-4 w-full cursor-not-allowed rounded-xl border border-border bg-muted/35 px-4 py-2.5 text-xs font-semibold text-muted-foreground">Executar Advisor — indisponível nesta etapa</button>
        </div>
      </section>
    </details>
  );
}

export function WealthHomeExperience() {
  const { selection } = useTransientAnalysis();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentMonth = getCurrentReferenceMonth();
  const rawMonth = searchParams.get("month");
  const { month: referenceMonth } = resolveReferenceMonth(rawMonth);
  const searchParamsString = searchParams.toString();
  const healthSearchParams = new URLSearchParams(searchParamsString);
  healthSearchParams.set("month", referenceMonth);
  const healthHref = buildHrefWithSearchParams(
    "/wealth-intelligence/health",
    healthSearchParams,
  );
  const [mode, setMode] = useState<WealthHomeMode>("authenticated");
  const [previewState, setPreviewState] = useState<WealthHomePreviewState>("success");
  const [reloadVersion, setReloadVersion] = useState(0);
  const [loadState, setLoadState] = useState<AuthenticatedLoadState>({ status: "loading" });
  const requestSequence = useRef(0);

  useEffect(() => {
    if (rawMonth === referenceMonth) return;
    const normalized = new URLSearchParams(searchParamsString);
    normalized.set("month", referenceMonth);
    router.replace(`${pathname}?${normalized.toString()}`, { scroll: false });
  }, [pathname, rawMonth, referenceMonth, router, searchParamsString]);

  const changeReferenceMonth = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const resolved = resolveReferenceMonth(event.currentTarget.value);
      if (resolved.issue !== null) return;
      const next = new URLSearchParams(searchParamsString);
      next.set("month", resolved.month);
      router.push(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [pathname, router, searchParamsString],
  );

  const retry = useCallback(() => {
    setReloadVersion((version) => version + 1);
  }, []);

  useEffect(() => {
    if (mode !== "authenticated") return;

    const sequence = ++requestSequence.current;
    setLoadState({ status: "loading" });
    loadWealthHome(referenceMonth).then(
      (data) => {
        if (sequence === requestSequence.current) setLoadState({ status: "success", data });
      },
      () => {
        if (sequence === requestSequence.current) setLoadState({ status: "error" });
      },
    );
    return () => {
      if (sequence === requestSequence.current) requestSequence.current += 1;
    };
  }, [mode, referenceMonth, reloadVersion]);

  const authenticatedData = loadState.status === "success" ? loadState.data : undefined;
  return (
    <div className="space-y-6 pb-8">
      <header className="rounded-2xl border border-border bg-gradient-to-r from-emerald-500/[0.07] via-white/[0.015] to-sky-500/[0.05] p-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">Inteligência Patrimonial</h1>
            <SourceBadge mode={mode} />
            {mode === "demo" ? <span className="text-[10px] text-muted-foreground">Fixture: {fixture.fixtureId}</span> : null}
          </div>
          <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center xl:w-auto">
            <MonthSelector
              value={referenceMonth}
              maximum={currentMonth}
              onChange={changeReferenceMonth}
            />
            <ModeSelector value={mode} onChange={setMode} />
            {mode === "demo" ? (
              <PreviewStateSelector value={previewState} onChange={setPreviewState} />
            ) : null}
          </div>
        </div>
      </header>

      {mode === "authenticated" && loadState.status === "loading" ? (
        <LoadingState authenticated />
      ) : null}
      {mode === "authenticated" && loadState.status === "error" ? (
        <ErrorState onRetry={retry} />
      ) : null}

      {mode === "demo" && previewState === "loading" ? <LoadingState /> : null}
      {mode === "demo" && previewState === "empty" ? <EmptyState /> : null}
      {mode === "demo" && previewState === "error" ? (
        <ErrorState authenticated={false} onRetry={() => setPreviewState("success")} />
      ) : null}

      {(mode === "authenticated" && loadState.status === "success") ||
      (mode === "demo" && previewState === "success") ? (
        <>
          <OverviewMetrics mode={mode} data={authenticatedData} healthHref={healthHref} selection={selection} />
          {mode === "authenticated" ? <PlanningAndFireEntryPoints selection={selection} /> : null}
          {mode === "authenticated" ? <TransientAnalysisPanel /> : null}
          {mode === "authenticated" ? (
            <GovernedInvestmentVisualizationsUnavailable />
          ) : (
            <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
              <InvestmentWealthChart />
              <AllocationView />
            </section>
          )}
          <AdvisorPreview />
        </>
      ) : null}
    </div>
  );
}
