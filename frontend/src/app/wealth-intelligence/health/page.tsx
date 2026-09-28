"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";

import { CategoryExpenseSection } from "./components/CategoryExpenseSection";
import { CategoryTrendSection } from "./components/CategoryTrendSection";
import { HealthHistorySection } from "./components/HealthHistorySection";
import { HealthSummaryCards } from "./components/HealthSummaryCards";
import { SpendingAnomalySection } from "./components/SpendingAnomalySection";
import type {
  CashflowSummary,
  CategoryExpenseSummary,
  FinancialTrendResponse,
  HistoricalFinancialMetric,
  SpendingAnomalySummary,
} from "./types";

type HealthData = {
  cashflow: CashflowSummary;
  history: HistoricalFinancialMetric[];
  categories: CategoryExpenseSummary;
  anomalies: SpendingAnomalySummary;
  trends: FinancialTrendResponse;
};

function currentReferenceMonth() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function HealthLoadingState() {
  return (
    <div aria-label="Carregando Saúde Financeira" aria-live="polite" className="space-y-5">
      <span className="sr-only">Carregando dados de Saúde Financeira.</span>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className="h-[154px] animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.025]"
          />
        ))}
      </div>
      <div className="h-[440px] animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.025]" />
      <div className="grid gap-5 xl:grid-cols-2">
        <div className="h-[360px] animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.025]" />
        <div className="h-[360px] animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.025]" />
      </div>
    </div>
  );
}

export default function FinancialHealthPage() {
  const [referenceMonth, setReferenceMonth] = useState(currentReferenceMonth);
  const [data, setData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestSequence = useRef(0);

  const loadHealth = useCallback(async () => {
    const requestId = ++requestSequence.current;
    setLoading(true);
    setError(null);

    try {
      const query = `?reference_month=${encodeURIComponent(referenceMonth)}`;
      const [cashflow, history, categories, anomalies, trends] = await Promise.all([
        fetchFromAPI<CashflowSummary>(`/financial-health/cashflow${query}`),
        fetchFromAPI<HistoricalFinancialMetric[]>(`/financial-health/history${query}`),
        fetchFromAPI<CategoryExpenseSummary>(`/financial-health/categories${query}`),
        fetchFromAPI<SpendingAnomalySummary>(`/financial-health/anomalies${query}`),
        fetchFromAPI<FinancialTrendResponse>(`/financial-health/trends${query}`),
      ]);

      if (!cashflow || !history || !categories || !anomalies || !trends) {
        throw new Error("Financial Health response is incomplete");
      }

      if (requestId !== requestSequence.current) return;
      setData({ cashflow, history, categories, anomalies, trends });
    } catch {
      if (requestId !== requestSequence.current) return;
      setData(null);
      setError("Não foi possível carregar os dados de Saúde Financeira.");
    } finally {
      if (requestId === requestSequence.current) {
        setLoading(false);
      }
    }
  }, [referenceMonth]);

  useEffect(() => {
    void loadHealth();
    return () => {
      requestSequence.current += 1;
    };
  }, [loadHealth]);

  return (
    <PageLayout hideTitle>
      <div className="space-y-6">
        <header className="flex justify-end border-b border-white/[0.06] pb-4">
          <h1 className="sr-only">Saúde Financeira</h1>
          <label className="flex w-full flex-col gap-1.5 text-xs font-medium text-zinc-400 sm:w-auto">
            Mês de referência
            <input
              aria-label="Mês de referência"
              type="month"
              value={referenceMonth}
              onChange={(event) => setReferenceMonth(event.target.value)}
              className="min-h-10 w-full rounded-xl border border-white/[0.12] bg-zinc-900 px-3 text-sm text-zinc-100 outline-none transition focus:border-sky-400/50 focus:ring-2 focus:ring-sky-400/10 sm:w-[190px]"
            />
          </label>
        </header>

        {error ? (
          <section
            role="alert"
            className="flex flex-col items-start justify-between gap-4 rounded-2xl border border-rose-400/20 bg-rose-400/[0.055] p-5 sm:flex-row sm:items-center"
          >
            <div>
              <p className="text-sm font-medium text-rose-200">Dados indisponíveis</p>
              <p className="mt-1 text-xs text-zinc-400">{error}</p>
            </div>
            <button
              type="button"
              onClick={() => void loadHealth()}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-rose-300/20 bg-rose-300/[0.07] px-4 text-xs font-semibold text-rose-200 transition hover:bg-rose-300/[0.12] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-300/40"
            >
              <RefreshCw aria-hidden="true" size={14} />
              Tentar novamente
            </button>
          </section>
        ) : null}

        {loading ? <HealthLoadingState /> : null}

        {!loading && !error && data ? (
          <main className="space-y-5">
            <HealthSummaryCards cashflow={data.cashflow} trends={data.trends} />
            <HealthHistorySection key={data.cashflow.reference_month} history={data.history} />
            <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <CategoryExpenseSection summary={data.categories} />
              <SpendingAnomalySection summary={data.anomalies} />
            </div>
            <CategoryTrendSection trends={data.trends} />
          </main>
        ) : null}
      </div>
    </PageLayout>
  );
}
