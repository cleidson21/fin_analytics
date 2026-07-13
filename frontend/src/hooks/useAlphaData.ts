import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";
import { PortfolioEvolutionPoint, PortfolioEvolutionSummary } from "./useGrowthData";

import { PerformanceSummary } from "./usePerformanceData";

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
        // Fetch real history
        const historyRes = await fetchFromAPI<{points: PortfolioEvolutionPoint[], summary: any}>("/investments/performance/history");
        
        const perfRes = await fetchFromAPI<PerformanceSummary>("/investments/performance");

        if (!mounted) return;
        if (perfRes && historyRes) {
          setHistory(historyRes.points || []);
          setSummary({
            patrimonio_atual: String(perfRes.market_value),
            patrimonio_atual_value: Number(perfRes.market_value || 0),
            rentabilidade_acumulada: Number(perfRes.metrics?.cagr || 0),
            proventos_totais: Number(perfRes.dividends_received || 0),
            compras_totais: Number(perfRes.cost_basis || 0),
            vendas_totais: 0,
            ibov_acumulado_pct: 0,
            cdi_acumulado_pct: 0,
            alpha_vs_ibov: Number(perfRes.metrics?.cagr || 0),
            alpha_vs_cdi: Number(perfRes.metrics?.cagr || 0)
          });
        } else {
          setIsError(true);
        }
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
