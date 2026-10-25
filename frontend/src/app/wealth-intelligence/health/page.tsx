"use client";

import { Suspense, type ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { RefreshCw } from "lucide-react";

import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { getCurrentReferenceMonth, resolveReferenceMonth } from "@/lib/wealthHome";

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

const pendingHealthReads = new Map<string, Promise<HealthData>>();

export function loadFinancialHealth(referenceMonth: string): Promise<HealthData> {
  const pending = pendingHealthReads.get(referenceMonth);
  if (pending) return pending;

  const query = `?reference_month=${encodeURIComponent(referenceMonth)}`;
  const request = Promise.all([
    fetchFromAPI<CashflowSummary>(`/financial-health/cashflow${query}`),
    fetchFromAPI<HistoricalFinancialMetric[]>(`/financial-health/history${query}`),
    fetchFromAPI<CategoryExpenseSummary>(`/financial-health/categories${query}`),
    fetchFromAPI<SpendingAnomalySummary>(`/financial-health/anomalies${query}`),
    fetchFromAPI<FinancialTrendResponse>(`/financial-health/trends${query}`),
  ]).then(([cashflow, history, categories, anomalies, trends]) => {
    if (!cashflow || !history || !categories || !anomalies || !trends) {
      throw new Error("Financial Health response is incomplete");
    }
    return { cashflow, history, categories, anomalies, trends };
  });

  pendingHealthReads.set(referenceMonth, request);
  const clearPending = () => {
    if (pendingHealthReads.get(referenceMonth) === request) {
      pendingHealthReads.delete(referenceMonth);
    }
  };
  void request.then(clearPending, clearPending);
  return request;
}

function HealthLoadingState() {
  return (
    <div aria-label="Carregando Saúde Financeira" aria-live="polite" className="space-y-5">
      <span className="sr-only">Carregando dados de Saúde Financeira.</span>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className="h-[154px] animate-pulse rounded-2xl border border-border bg-muted/30"
          />
        ))}
      </div>
      <div className="h-[440px] animate-pulse rounded-2xl border border-border bg-muted/30" />
      <div className="grid gap-5 xl:grid-cols-2">
        <div className="h-[360px] animate-pulse rounded-2xl border border-border bg-muted/30" />
        <div className="h-[360px] animate-pulse rounded-2xl border border-border bg-muted/30" />
      </div>
    </div>
  );
}

export function FinancialHealthExperience() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsString = searchParams.toString();
  const rawMonth = searchParams.get("month");
  const { month: referenceMonth } = resolveReferenceMonth(rawMonth);
  const currentMonth = getCurrentReferenceMonth();
  const [data, setData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

  const loadHealth = useCallback(async () => {
    const requestId = ++requestSequence.current;
    setLoading(true);
    setError(null);

    try {
      const nextData = await loadFinancialHealth(referenceMonth);

      if (requestId !== requestSequence.current) return;
      setData(nextData);
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
      <div className="space-y-5">
        <header className="flex items-center justify-between gap-3 border-b border-border pb-3">
          <h1 className="sr-only">Saúde Financeira</h1>
          <p className="text-sm font-semibold text-foreground">Saúde Financeira</p>
          <label className="flex w-full flex-col gap-1.5 text-xs font-medium text-muted-foreground sm:w-auto">
            Mês de referência
            <input
              aria-label="Mês de referência"
              type="month"
              value={referenceMonth}
              max={currentMonth}
              onChange={changeReferenceMonth}
              className="min-h-10 w-full rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-sky-400/50 focus:ring-2 focus:ring-sky-400/10 sm:w-[190px]"
            />
          </label>
        </header>

        {error ? (
          <section
            role="alert"
            className="flex flex-col items-start justify-between gap-4 rounded-2xl border border-rose-400/20 bg-rose-400/[0.055] p-5 sm:flex-row sm:items-center"
          >
            <div>
              <p className="text-sm font-medium text-destructive">Dados indisponíveis</p>
              <p className="mt-1 text-xs text-muted-foreground">{error}</p>
            </div>
            <button
              type="button"
              onClick={() => void loadHealth()}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-rose-300/20 bg-rose-300/[0.07] px-4 text-xs font-semibold text-destructive transition hover:bg-rose-300/[0.12] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-300/40"
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

export default function FinancialHealthPage() {
  return (
    <Suspense fallback={<HealthLoadingState />}>
      <FinancialHealthExperience />
    </Suspense>
  );
}
