"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Line, LineChart } from "recharts";

import { PageLayout } from "@/components/layout/PageLayout";
import { requestLedgerFromAPI as fetchFromAPI, isLedgerAuthorizationError, LEDGER_AUTHORIZATION_PENDING } from "@/lib/ledgerApi";
import { getCategoryColor } from "@/lib/colors";
import { addMonths, getCurrentMonth, getMonthBounds } from "@/lib/period";
import { formatCurrency, colorForValue } from "@/lib/utils";
import { DeltaBadge } from "@/components/ui/DeltaBadge";
import type { RawData, GovernanceData } from "@/components/governance/TransactionGovernanceModal";

interface PierreImportResponse {
  success: boolean;
  transactions: number;
  skipped?: number;
  errors?: number;
  status?: string;
  error_message?: string;
}

interface KpiItem {
  current: number;
  previous: number;
  delta_pct: number;
}

interface DashboardSummaryV2 {
  month: string;
  receitas: KpiItem;
  despesas: KpiItem;
  saldo_liquido: KpiItem;
  patrimonio: KpiItem;
}

interface DailyDataPoint {
  date: string;
  current_amount: number;
  previous_amount: number;
}

interface PacingV2 {
  current_month: string;
  previous_month: string;
  current_expenses: number;
  previous_expenses: number;
  delta_percentage: number;
  trend: string;
  severity: string;
  message: string;
  daily_data: DailyDataPoint[];
}

interface HeatmapDay {
  date: string;
  amount: string;
  intensity: number;
}

interface CategoryBreakdown {
  category: string;
  total: number;
}

interface TransactionItem {
  id: string;
  date: string;
  description: string;
  category: string;
  natureza: string;
  subnatureza: string;
  account: string;
  amount: number | string;
}

interface TransactionListResponse {
  items: TransactionItem[];
}

type LoadState = {
  summary: boolean;
  pacing: boolean;
  heatmap: boolean;
  categories: boolean;
  transactions: boolean;
};

function toNumber(value: number | string | null | undefined): number {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function formatDelta(delta: number) {
  const prefix = delta > 0 ? "+" : "";
  return `${prefix}${delta.toFixed(1)}%`;
}


function categoryLabel(category: string) {
  return category.toLowerCase().replace(/_/g, " ");
}

function formatTxDate(value: string) {
  const dt = new Date(`${value}T00:00:00`);
  if (Number.isNaN(dt.getTime())) {
    return value;
  }

  return dt.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

function getTxVisual(tx: TransactionItem) {
  const ec = tx.natureza?.toUpperCase();
  if (ec === "ENTRADA") {
    return { icon: "↗", box: "bg-green-500/15 text-green-300", value: "text-green-400" };
  }

  if (ec === "SAIDA") {
    return { icon: "↘", box: "bg-red-500/15 text-red-300", value: "text-red-400" };
  }

  if (ec === "IGNORAR") {
    return { icon: "→", box: "bg-white/[0.06] text-neutral-400", value: "text-neutral-400" };
  }

  // PENDING ou desconhecido
  return { icon: "↔", box: "bg-amber-500/10 text-amber-300", value: "text-amber-300" };
}

function LoadingBar({ width = "w-32" }: { width?: string }) {
  return <div className={`h-6 ${width} animate-pulse rounded bg-white/[0.04]`} />;
}

export function DashboardPage() {
  const router = useRouter();
  const chartWrapRef = useRef<HTMLDivElement | null>(null);
  const [chartWidth, setChartWidth] = useState<number>(0);

  const currentMonth = useMemo(() => getCurrentMonth(), []);
  const prevMonth = useMemo(() => addMonths(currentMonth, -1), [currentMonth]);
  const monthBounds = useMemo(() => getMonthBounds(currentMonth), [currentMonth]);

  const [summary, setSummary] = useState<DashboardSummaryV2 | null>(null);
  const [pacing, setPacing] = useState<PacingV2 | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapDay[] | null>(null);
  const [catsCurrent, setCatsCurrent] = useState<CategoryBreakdown[] | null>(null);
  const [catsPrev, setCatsPrev] = useState<CategoryBreakdown[] | null>(null);
  const [recentTxs, setRecentTxs] = useState<TransactionItem[] | null>(null);

  const [loading, setLoading] = useState<LoadState>({
    summary: true,
    pacing: true,
    heatmap: true,
    categories: true,
    transactions: true,
  });

  // ------------------------------------------------------------------ //
  //  Pierre import state
  // ------------------------------------------------------------------ //
  type ImportStatus = "idle" | "loading" | "success" | "error";
  interface ImportResult {
    status: string;
    imported: number;
    skipped: number;
    errors: number;
    duration_seconds?: number;
    error_message?: string;
  }

  const [importStatus, setImportStatus] = useState<ImportStatus>("idle");
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null);
  const [authorizationError, setAuthorizationError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const importBusy = useRef(false);

  useEffect(() => {
    setLastSyncAt(localStorage.getItem("pierre_last_sync"));
  }, []);

  const handleImportPierre = useCallback(async () => {
    if (importBusy.current) return;
    importBusy.current = true;
    setImportStatus("loading");
    setImportResult(null);
    try {
      const result = await fetchFromAPI<PierreImportResponse>("/pierre/import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ start_date: null, end_date: null }),
      });
      if (!result) throw new Error("Sem resposta do servidor");
      
      const success = result.success === true && (result.errors ?? 0) === 0
        && Number.isSafeInteger(result.transactions) && result.transactions >= 0
        && result.status !== "partial" && result.status !== "failed";
      const mappedResult: ImportResult = {
        status: success ? "success" : "failed",
        imported: result.transactions || 0,
        skipped: result.skipped ?? 0,
        errors: success ? 0 : 1,
        error_message: result.error_message || (success ? undefined : "Importação não concluída; confirme o resultado antes de tentar novamente")
      };
      
      setImportResult(mappedResult);
      setImportStatus(success ? "success" : "error");
      if (success) {
        setAuthorizationError(null);
        setRefreshKey((value) => value + 1);
        const now = new Date().toLocaleString("pt-BR");
        setLastSyncAt(now);
        if (typeof window !== "undefined") localStorage.setItem("pierre_last_sync", now);
      }
    } catch (err) {
      if (isLedgerAuthorizationError(err)) {
        setAuthorizationError(LEDGER_AUTHORIZATION_PENDING);
        setLastSyncAt(null);
      }
      setImportResult({ status: "failed", imported: 0, skipped: 0, errors: 1, error_message: err instanceof Error ? err.message : "Importação não concluída" });
      setImportStatus("error");
    } finally {
      importBusy.current = false;
    }
  }, []);

  useEffect(() => {
    const resize = () => {
      if (!chartWrapRef.current) {
        return;
      }
      setChartWidth(Math.max(0, Math.floor(chartWrapRef.current.clientWidth)));
    };

    resize();

    const observer = new ResizeObserver(() => resize());
    if (chartWrapRef.current) {
      observer.observe(chartWrapRef.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDashboardData() {
      const [summaryData, pacingData, heatmapData, categoriesCurrent, categoriesPrev, recentTransactions] = await Promise.allSettled([
        fetchFromAPI<DashboardSummaryV2>(`/dashboard/summary-v2?month=${currentMonth}`),
        fetchFromAPI<PacingV2>(`/dashboard/pacing-v2?month=${currentMonth}`),
        fetchFromAPI<HeatmapDay[]>(`/dashboard/heatmap?month=${currentMonth}`),
        fetchFromAPI<CategoryBreakdown[]>(`/dashboard/categories?month=${currentMonth}`),
        fetchFromAPI<CategoryBreakdown[]>(`/dashboard/categories?month=${prevMonth}`),
        // Usa governance/transactions para ter dados reais com nome de conta e data correta
        fetchFromAPI<{ items: { raw: RawData; governance: GovernanceData }[]; total: number }>("/governance/transactions?page_size=5"),
      ]);

      if (!active) {
        return;
      }

      const denied = [summaryData, pacingData, heatmapData, categoriesCurrent, categoriesPrev, recentTransactions]
        .some((result) => result.status === "rejected" && isLedgerAuthorizationError(result.reason));
      const failed = [summaryData, pacingData, heatmapData, categoriesCurrent, categoriesPrev, recentTransactions]
        .some((result) => result.status === "rejected");
      setAuthorizationError(denied ? LEDGER_AUTHORIZATION_PENDING : failed ? "Dados financeiros indisponíveis. Tente novamente." : null);
      if (failed) {
        setSummary(null); setPacing(null); setHeatmap(null);
        setCatsCurrent(null); setCatsPrev(null); setRecentTxs(null);
        setLastSyncAt(null);
        setLoading({ summary: false, pacing: false, heatmap: false, categories: false, transactions: false });
        return;
      }

      const getValue = <T,>(result: PromiseSettledResult<T | null>): T | null =>
        result.status === "fulfilled" ? result.value : null;

      setSummary(getValue(summaryData));
      setPacing(getValue(pacingData));
      setHeatmap(getValue(heatmapData) ?? []);
      setCatsCurrent(getValue(categoriesCurrent) ?? []);
      setCatsPrev(getValue(categoriesPrev) ?? []);

      // Mapeia do formato governance {raw, governance} para TransactionItem
      const rawTxs = getValue(recentTransactions)?.items ?? [];
      const mappedTxs: TransactionItem[] = rawTxs.map((t) => ({
        id: `${t.raw?.provider}::${t.raw?.external_id}`,
        date: (t.raw?.date ?? "").slice(0, 10),
        description: t.raw?.description ?? "",
        category: t.raw?.category ?? "",
        natureza: t.governance?.economic_classification ?? "",
        subnatureza: t.raw?.type ?? "",
        account: t.raw?.account_name || t.raw?.account_external_id || "",
        amount: t.raw?.amount ?? 0,
      }));
      setRecentTxs(mappedTxs);

      setLoading({
        summary: false,
        pacing: false,
        heatmap: false,
        categories: false,
        transactions: false,
      });
    }

    void loadDashboardData();

    return () => {
      active = false;
    };
  }, [currentMonth, prevMonth, refreshKey]);

  const pushTransactionsRange = (startDate: string, endDate: string, category?: string) => {
    const base = `/transactions?startDate=${encodeURIComponent(startDate)}&endDate=${encodeURIComponent(endDate)}`;
    const withCategory = category ? `${base}&category=${encodeURIComponent(category)}` : base;
    router.push(withCategory);
  };

  const categoryStats = useMemo(() => {
    const current = (catsCurrent ?? []).slice().sort((a, b) => b.total - a.total);
    const prevMap = new Map((catsPrev ?? []).map((item) => [item.category, item.total]));

    const ranked = current.map((item) => {
      const previous = prevMap.get(item.category);
      const hasPrevious = typeof previous === "number";
      const delta = hasPrevious && previous !== 0 ? ((item.total - previous) / Math.abs(previous)) * 100 : null;

      return {
        category: item.category,
        current: item.total,
        previous: previous ?? 0,
        delta,
        isNew: !hasPrevious,
      };
    });

    const top5 = ranked.slice(0, 5);
    const highestPositive = ranked
      .filter((item) => item.delta !== null && item.delta > 0)
      .sort((a, b) => (b.delta ?? 0) - (a.delta ?? 0))[0];

    return { top5, highestPositive };
  }, [catsCurrent, catsPrev]);

  const { insightsTitle, titleColor } = useMemo(() => {
    if (categoryStats.highestPositive?.delta !== null && categoryStats.highestPositive?.delta !== undefined) {
      return {
        insightsTitle: `${categoryLabel(categoryStats.highestPositive.category)} subiu ${categoryStats.highestPositive.delta.toFixed(0)}%. Bora revisar?`,
        titleColor: "text-[#f5a623]"
      };
    }

    const receitaDelta = summary?.receitas?.delta_pct ?? 0;
    const insightsTitle =
      receitaDelta > 0
        ? "Receitas a subir"
        : receitaDelta < 0
          ? "Receitas a recuar"
          : "Receitas estáveis";

    const titleColor = receitaDelta >= 0 ? "text-[#4ecf98]" : "text-[#f5a623]";

    return { insightsTitle, titleColor };
  }, [categoryStats.highestPositive, summary?.receitas?.delta_pct]);

  const heatmapGrid = useMemo(() => {
    const days = heatmap ?? [];
    if (days.length === 0) {
      return [] as Array<HeatmapDay | null>;
    }

    const firstWeekday = new Date(`${days[0].date}T00:00:00`).getDay();
    return [...Array(firstWeekday).fill(null), ...days];
  }, [heatmap]);

  const heatmapTotals = useMemo(() => {
    const days = heatmap ?? [];
    const total = days.reduce((acc, day) => acc + toNumber(day.amount), 0);
    const average = days.length > 0 ? total / days.length : 0;
    return { total, average };
  }, [heatmap]);

  const resolvedChartWidth = chartWidth > 0 ? chartWidth : 320;

  if (authorizationError) {
    return (
      <PageLayout title="Visão Geral" subtitle={`Dados do mês: ${currentMonth}`} hideTitle={true}>
        <div role="alert" className="rounded-xl border border-white/10 p-4 text-sm text-neutral-300">
          <p>{authorizationError}</p>
          <button type="button" onClick={handleImportPierre} disabled={importStatus === "loading"} className="mt-3 rounded-lg border border-white/10 px-3 py-2">
            {importStatus === "loading" ? "Importando…" : "Importar Dados"}
          </button>
          {importStatus === "error" && importResult && <p className="mt-2">{importResult.error_message ?? "Importação não concluída"}</p>}
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Visão Geral" subtitle={`Dados do mês: ${currentMonth}`} hideTitle={true}>
      <div className="space-y-6 text-white">

        {/* Pierre import bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-[#111] px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#4ecf98]/10">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 text-[#4ecf98]">
                <path d="M10.75 2.75a.75.75 0 0 0-1.5 0v8.614L6.295 8.235a.75.75 0 1 0-1.09 1.03l4.25 4.5a.75.75 0 0 0 1.09 0l4.25-4.5a.75.75 0 0 0-1.09-1.03l-2.955 3.129V2.75Z" />
                <path d="M3.5 12.75a.75.75 0 0 0-1.5 0v2.5A2.75 2.75 0 0 0 4.75 18h10.5A2.75 2.75 0 0 0 18 15.25v-2.5a.75.75 0 0 0-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5Z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-medium text-neutral-300">Sincronizar Pierre Finance</p>
              {lastSyncAt && (
                <p className="text-[10px] text-neutral-500">Última sync: {lastSyncAt}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {importStatus === "success" && importResult && (
              <span className="text-xs text-[#4ecf98]">
                ✓ {importResult.imported} importadas, {importResult.skipped} ignoradas
              </span>
            )}
            {importStatus === "error" && importResult && (
              <span className="text-xs text-[#e97070]">
                ✗ {importResult.error_message ?? "Erro na importação"}
              </span>
            )}
            <button
              type="button"
              onClick={handleImportPierre}
              disabled={importStatus === "loading"}
              className="flex items-center gap-2 rounded-lg bg-[#4ecf98]/10 px-3 py-1.5 text-xs font-medium text-[#4ecf98] transition hover:bg-[#4ecf98]/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {importStatus === "loading" ? (
                <>
                  <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Importando…
                </>
              ) : (
                "Importar Dados"
              )}
            </button>
          </div>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {loading.summary || !summary ? (
            Array.from({ length: 4 }).map((_, index) => (
              <article key={`kpi-loading-${index}`} className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <LoadingBar width="w-24" />
                <div className="mt-3">
                  <LoadingBar width="w-36" />
                </div>
              </article>
            ))
          ) : (
            [
              { label: "Patrimônio Total", value: summary.patrimonio, color: colorForValue(summary.patrimonio.current), isExpense: false },
              { label: "Receitas", value: summary.receitas, color: "text-[#4ecf98]", isExpense: false },
              { label: "Despesas", value: summary.despesas, color: "text-[#e97070]", isExpense: true },
              { label: "Saldo Líquido", value: summary.saldo_liquido, color: colorForValue(summary.saldo_liquido.current), isExpense: false },
            ].map((item) => (
              <article key={item.label} className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <p className="text-xs uppercase tracking-widest text-neutral-500">{item.label}</p>
                <p className={`mt-3 text-xl font-medium ${item.color}`}>{formatCurrency(item.value.current)}</p>
                <div className="mt-3">
                  <DeltaBadge value={item.value.delta_pct} invertido={item.isExpense} />
                </div>
              </article>
            ))
          )}
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <article
            className="cursor-pointer rounded-xl border border-white/[0.07] border-l-2 border-l-[#4ecf98] bg-gradient-to-br from-[#1a2620] to-[#1a1a1a] p-4"
            onClick={() => pushTransactionsRange(monthBounds.startDate, monthBounds.endDate)}
          >
            {loading.summary || !summary ? (
              <div className="space-y-3">
                <LoadingBar width="w-60" />
                <LoadingBar width="w-44" />
                <div className="grid gap-2 sm:grid-cols-3">
                  <LoadingBar width="w-full" />
                  <LoadingBar width="w-full" />
                  <LoadingBar width="w-full" />
                </div>
              </div>
            ) : (
              <>
                <h3 className={`text-3xl font-semibold leading-tight ${titleColor}`}>{insightsTitle}</h3>
                <p className="mt-2 text-sm text-neutral-400">Gerado para o mês atual.</p>

                <div className="mt-4 grid gap-2 sm:grid-cols-3">
                  <div className="rounded-lg border border-white/[0.05] bg-white/[0.03] p-3">
                    <p className="text-xs text-neutral-500">Gasto Mai.</p>
                    <p className="mt-1 text-lg font-medium text-white">{formatCurrency(summary.despesas.current)}</p>
                  </div>
                  <div className="rounded-lg border border-white/[0.05] bg-white/[0.03] p-3">
                    <p className="text-xs text-neutral-500">Variação %</p>
                    <p className="mt-1 text-lg font-medium text-white">{formatDelta(summary.despesas.delta_pct)}</p>
                  </div>
                  <div className="rounded-lg border border-white/[0.05] bg-white/[0.03] p-3">
                    <p className="text-xs text-neutral-500">Maior categoria</p>
                    <p className="mt-1 text-lg font-medium capitalize text-white">
                      {categoryStats.top5[0] ? categoryLabel(categoryStats.top5[0].category) : "-"}
                    </p>
                  </div>
                </div>
              </>
            )}
          </article>

          <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="text-xs uppercase tracking-widest text-neutral-500">Ritmo de Gastos</p>
              <button
                type="button"
                onClick={() => pushTransactionsRange(monthBounds.startDate, monthBounds.endDate)}
                className="cursor-pointer text-xs text-neutral-600 transition hover:text-neutral-400"
              >
                ver todas ↗
              </button>
            </div>

            {loading.pacing || !pacing ? (
              <div className="mt-4 space-y-3">
                <LoadingBar width="w-36" />
                <LoadingBar width="w-24" />
                <LoadingBar width="w-full" />
              </div>
            ) : (
              <>
                <div className="mt-4 flex items-end justify-between gap-4">
                  <p className="text-3xl font-semibold text-white">{formatCurrency(pacing.current_expenses)}</p>
                  <DeltaBadge value={pacing.delta_percentage} invertido={true} />
                </div>

                <div ref={chartWrapRef} className="mt-4" style={{ width: "100%" }}>
                  <LineChart width={resolvedChartWidth} height={70} data={pacing.daily_data}>
                    <Line dataKey="current_amount" stroke="#4ecf98" dot={false} strokeWidth={2} />
                    <Line
                      dataKey="previous_amount"
                      stroke="#444"
                      dot={false}
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                    />
                  </LineChart>
                </div>

                <div className="mt-3 flex items-center gap-4 text-xs text-neutral-500">
                  <span className="inline-flex items-center gap-1">
                    <span className="h-[2px] w-4 bg-[#4ecf98]" />
                    Este mês
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="h-[2px] w-4 bg-[#444]" />
                    Mês passado
                  </span>
                </div>
              </>
            )}
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-widest text-neutral-500">Mapa de Calor</p>
                {loading.heatmap || !heatmap ? (
                  <div className="mt-2 space-y-2">
                    <LoadingBar width="w-32" />
                    <LoadingBar width="w-28" />
                  </div>
                ) : (
                  <>
                    <p className="mt-2 text-3xl font-semibold text-white">{formatCurrency(heatmapTotals.total)}</p>
                    <p className="text-sm text-neutral-500">Média diária: {formatCurrency(heatmapTotals.average)}</p>
                  </>
                )}
              </div>
              <button
                type="button"
                onClick={() => pushTransactionsRange(monthBounds.startDate, monthBounds.endDate)}
                className="cursor-pointer text-xs text-neutral-600 transition hover:text-neutral-400"
              >
                ver mais ↗
              </button>
            </div>

            {loading.heatmap || !heatmap ? (
              <div className="mt-4 grid grid-cols-7 gap-1">
                {Array.from({ length: 35 }).map((_, index) => (
                  <div key={`heat-loading-${index}`} className="h-[22px] animate-pulse rounded-[3px] bg-white/[0.04]" />
                ))}
              </div>
            ) : (
              <>
                <div className="mt-4 grid grid-cols-7 gap-1 text-center text-xs text-neutral-600">
                  {"DSTQQSS".split("").map((day, index) => (
                    <span key={`${day}-${index}`}>{day}</span>
                  ))}
                </div>

                <div className="mt-2 grid grid-cols-7 gap-1">
                  {heatmapGrid.map((day, index) => {
                    if (!day) {
                      return <div key={`empty-${index}`} className="h-[22px] rounded-[3px] bg-transparent" />;
                    }

                    const dayNumber = new Date(`${day.date}T00:00:00`).getDate();

                    if (day.intensity <= 0) {
                      return (
                        <div
                          key={day.date}
                          className="flex h-[22px] cursor-default items-center justify-center rounded-[3px] bg-[#1e1e1e] text-[10px] font-medium text-white"
                        >
                          {dayNumber}
                        </div>
                      );
                    }

                    return (
                      <button
                        type="button"
                        key={day.date}
                        className="flex h-[22px] cursor-pointer items-center justify-center rounded-[3px] text-[10px] font-medium text-white transition-all hover:brightness-125"
                        style={{ background: `rgba(216,90,48,${Math.max(0.08, day.intensity)})` }}
                        onClick={() => pushTransactionsRange(day.date, day.date)}
                        aria-label={`Abrir transações do dia ${day.date}`}
                      >
                        {dayNumber}
                      </button>
                    );
                  })}
                </div>

                <div className="mt-4 flex items-center justify-end gap-2 text-xs text-neutral-600">
                  <span>Menos</span>
                  {[0.12, 0.3, 0.5, 0.7, 0.95].map((alpha, index) => (
                    <span
                      key={`legend-${index}`}
                      className="h-3 w-3 rounded-[2px]"
                      style={{ background: `rgba(216,90,48,${alpha})` }}
                    />
                  ))}
                  <span>Mais</span>
                </div>
              </>
            )}
          </article>

          <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="text-xs uppercase tracking-widest text-neutral-500">Principais Categorias</p>
              <button
                type="button"
                onClick={() => router.push("/categories")}
                className="cursor-pointer text-xs text-neutral-600 transition hover:text-neutral-400"
              >
                ver mais ↗
              </button>
            </div>

            <div className="mt-3 grid grid-cols-[1.6fr_1fr_1fr_1fr] gap-2 text-xs text-neutral-600">
              <span>Categoria</span>
              <span className="text-right">Atual</span>
              <span className="text-right">Variação</span>
              <span className="text-right">Anterior</span>
            </div>

            {loading.categories || !catsCurrent || !catsPrev ? (
              <div className="mt-3 space-y-2">
                {Array.from({ length: 5 }).map((_, index) => (
                  <LoadingBar key={`cat-loading-${index}`} width="w-full" />
                ))}
              </div>
            ) : (
              <div className="mt-2">
                {categoryStats.top5.map((item, index) => {
                  const badgeClass = item.delta === null
                    ? "bg-white/[0.06] text-neutral-500"
                    : item.delta < 0
                      ? "bg-green-500/10 text-green-400"
                      : item.delta > 0
                        ? "bg-red-500/10 text-red-400"
                        : "bg-white/[0.06] text-neutral-500";

                  return (
                    <button
                      type="button"
                      key={item.category}
                      onClick={() => pushTransactionsRange(monthBounds.startDate, monthBounds.endDate, item.category)}
                      className="grid w-full grid-cols-[1.6fr_1fr_1fr_1fr] items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-white/[0.03]"
                    >
                      <span className="inline-flex items-center gap-2 text-sm text-white">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: getCategoryColor(item.category, index) }}
                        />
                        <span className="capitalize">{categoryLabel(item.category)}</span>
                      </span>
                      <span className="text-right text-sm text-white">{formatCurrency(item.current)}</span>
                      <span className="text-right">
                        <span className={`inline-flex rounded-full px-2 py-1 text-[11px] ${badgeClass}`}>
                          {item.isNew || item.delta === null ? "novo" : formatDelta(item.delta)}
                        </span>
                      </span>
                      <span className="text-right text-sm text-neutral-400">{formatCurrency(item.previous)}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </article>
        </section>

        <section className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
          <div className="flex items-start justify-between gap-3">
            <p className="text-xs uppercase tracking-widest text-neutral-500">Transações Recentes</p>
            <button
              type="button"
              onClick={() => pushTransactionsRange(monthBounds.startDate, monthBounds.endDate)}
              className="cursor-pointer text-xs text-neutral-600 transition hover:text-neutral-400"
            >
              ver todas ↗
            </button>
          </div>

          {loading.transactions || !recentTxs ? (
            <div className="mt-4 space-y-3">
              {Array.from({ length: 5 }).map((_, index) => (
                <LoadingBar key={`tx-loading-${index}`} width="w-full" />
              ))}
            </div>
          ) : (
            <div className="mt-4">
              {recentTxs.slice(0, 5).map((tx, index, list) => {
                const visual = getTxVisual(tx);
                const amount = toNumber(tx.amount);

                return (
                  <article
                    key={tx.id}
                    className={`flex items-center justify-between gap-3 py-3 ${index < list.length - 1 ? "border-b border-white/[0.05]" : ""}`}
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <div className={`flex h-5 w-5 items-center justify-center rounded ${visual.box}`}>
                        <span className="text-[10px] leading-none">{visual.icon}</span>
                      </div>

                      <div className="min-w-0">
                        <p className="truncate text-sm text-white">{tx.description}</p>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-neutral-500">
                          <span className="rounded bg-white/[0.06] px-1.5 py-0.5">{categoryLabel(tx.category)}</span>
                          <span>{tx.account}</span>
                          <span>{formatTxDate(tx.date)}</span>
                        </div>
                      </div>
                    </div>

                    <p className={`whitespace-nowrap text-base font-medium ${visual.value}`}>
                      {formatCurrency(amount)}
                    </p>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </PageLayout>
  );
}
