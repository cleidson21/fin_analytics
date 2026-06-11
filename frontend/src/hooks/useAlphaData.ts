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
      } catch {
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

  // Lógica de Rebase: Subtrair o acumulado do primeiro mês do período
  // para que todas as linhas comecem do zero relativo ao período filtrado.
  const rebasedHistory = filteredHistory.map((point, index) => {
    if (index === 0 || !filteredHistory[0]) return { ...point, rebased_cart: 0, rebased_ibov: 0, rebased_cdi: 0, rebased_ipca: 0, rebased_ifix: 0, rebased_sp500: 0, rebased_idiv: 0 };
    
    const base = filteredHistory[0];
    return {
      ...point,
      rebased_cart: point.rentabilidade_acumulada_pct - base.rentabilidade_acumulada_pct,
      rebased_ibov: point.ibov_acumulado_pct - base.ibov_acumulado_pct,
      rebased_cdi: point.cdi_acumulado_pct - base.cdi_acumulado_pct,
      rebased_ipca: point.ipca_acumulado_pct - base.ipca_acumulado_pct,
      rebased_ifix: point.ifix_acumulado_pct - base.ifix_acumulado_pct,
      rebased_sp500: point.sp500_acumulado_pct - base.sp500_acumulado_pct,
      rebased_idiv: point.idiv_acumulado_pct - base.idiv_acumulado_pct
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
