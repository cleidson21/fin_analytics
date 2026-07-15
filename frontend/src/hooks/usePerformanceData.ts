import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";

export interface PerformanceMetrics {
  unrealized_gain: number;
  realized_gain: number;
  total_gain: number;
  dividends_received: number;
  total_return: number;
  unrealized_return_pct: number;
  realized_return_pct: number;
  total_return_pct: number;
  yield_on_cost: number;
  cagr: number;
  annualized_return_pct: number;
  monthly_return_pct: number;
  daily_return_pct: number;
  mwr: number;
  twr: number;
}

export interface PerformanceSummary {
  cost_basis: number;
  market_value: number;
  metrics: PerformanceMetrics;
  holding_days: number;
}

let performancePromiseCache: Promise<PerformanceSummary | null> | null = null;
let lastFetchTime = 0;

export async function fetchPerformanceDataShared(): Promise<PerformanceSummary | null> {
  const now = Date.now();
  if (performancePromiseCache && (now - lastFetchTime < 5000)) {
    return performancePromiseCache;
  }
  
  const promise = fetchFromAPI<any>("/investments/evolution/summary").then(res => {
    if (!res) return null;
    return {
      cost_basis: Number(res.total_invested || 0),
      market_value: Number(res.current_wealth || 0),
      holding_days: 0,
      metrics: {
        unrealized_gain: Number(res.current_wealth || 0) - Number(res.total_invested || 0),
        realized_gain: 0,
        total_gain: Number(res.current_wealth || 0) - Number(res.total_invested || 0) + Number(res.total_dividends || 0),
        dividends_received: Number(res.total_dividends || 0),
        total_return: 0,
        unrealized_return_pct: 0,
        realized_return_pct: 0,
        total_return_pct: Number(res.accumulated_return_pct || 0),
        yield_on_cost: 0,
        cagr: Number(res.accumulated_return_pct || 0),
        annualized_return_pct: 0,
        monthly_return_pct: 0,
        daily_return_pct: 0,
        mwr: 0,
        twr: 0
      }
    };
  });

  performancePromiseCache = promise;
  lastFetchTime = now;
  
  try {
    const res = await performancePromiseCache;
    return res;
  } catch (err) {
    performancePromiseCache = null;
    throw err;
  }
}

export function usePerformanceData() {
  const [data, setData] = useState<PerformanceSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const res = await fetchPerformanceDataShared();
        if (!mounted) return;
        if (res) setData(res);
        else setIsError(true);
      } catch {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, []);

  return { data, isLoading, isError };
}
