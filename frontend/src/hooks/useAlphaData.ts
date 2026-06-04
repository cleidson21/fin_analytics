import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";
import { PortfolioEvolutionPoint, PortfolioEvolutionSummary } from "./useGrowthData";

export function useAlphaData(period: string) {
  const [history, setHistory] = useState<PortfolioEvolutionPoint[]>([]);
  const [summary, setSummary] = useState<PortfolioEvolutionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const [histRes, sumRes] = await Promise.all([
          fetchFromAPI<PortfolioEvolutionPoint[]>("/investments/evolution/history"),
          fetchFromAPI<PortfolioEvolutionSummary>("/investments/evolution/summary")
        ]);

        if (!mounted) return;
        if (histRes) setHistory(histRes);
        if (sumRes) setSummary(sumRes);
        if (!histRes || !sumRes) setIsError(true);
      } catch (err) {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, []);

  let filteredHistory = history;
  if (period !== "ALL" && history.length > 0) {
    let monthsToKeep = history.length;
    switch (period) {
      case "3M": monthsToKeep = 3; break;
      case "6M": monthsToKeep = 6; break;
      case "1A": monthsToKeep = 12; break;
      case "2A": monthsToKeep = 24; break;
    }
    filteredHistory = history.slice(Math.max(history.length - monthsToKeep, 0));
  }

  // To draw a proper alpha chart, we might need to rebase the accumulated percentages 
  // so they start from 0 at the beginning of the filtered period.
  // But for now we just pass the raw data and let the chart handle it or display it.
  const rebasedHistory = filteredHistory.map((point, index) => {
    if (index === 0 || !filteredHistory[0]) return { ...point, rebased_cart: 0, rebased_ibov: 0, rebased_cdi: 0 };
    
    // Rebase approach: Current accumulated - Initial accumulated of the period
    // This is an approximation, mathematically exact would require division, but subtraction is enough for visual trends of "alpha".
    const base = filteredHistory[0];
    return {
      ...point,
      rebased_cart: point.rentabilidade_acumulada_pct - base.rentabilidade_acumulada_pct,
      rebased_ibov: point.ibov_acumulado_pct - base.ibov_acumulado_pct,
      rebased_cdi: point.cdi_acumulado_pct - base.cdi_acumulado_pct,
      rebased_ipca: point.ipca_acumulado_pct - base.ipca_acumulado_pct
    };
  });

  return {
    history: rebasedHistory,
    rawHistory: filteredHistory,
    summary,
    isLoading,
    isError
  };
}
