import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";
// Let's define local types based on the backend schema.

export interface PortfolioEvolutionSummary {
  patrimonio_atual: string;
  patrimonio_atual_value: number;
  rentabilidade_acumulada: number;
  proventos_totais: number;
  compras_totais: number;
  vendas_totais: number;
  ibov_acumulado_pct: number;
  cdi_acumulado_pct: number;
  alpha_vs_ibov: number;
  alpha_vs_cdi: number;
}

export interface PortfolioEvolutionPoint {
  month: string;
  patrimonio: string;
  patrimonio_value: number;
  compras: string;
  compras_value: number;
  vendas: string;
  vendas_value: number;
  proventos: string;
  proventos_value: number;
  rentabilidade_mensal_pct: number;
  rentabilidade_acumulada_pct: number;
  ibov_mensal_pct: number;
  ibov_acumulado_pct: number;
  cdi_mensal_pct: number;
  cdi_acumulado_pct: number;
  ipca_mensal_pct: number;
  ipca_acumulado_pct: number;
  ifix_mensal_pct: number;
  ifix_acumulado_pct: number;
  sp500_mensal_pct: number;
  sp500_acumulado_pct: number;
  idiv_mensal_pct: number;
  idiv_acumulado_pct: number;
}

import { PerformanceSummary, fetchPerformanceDataShared } from "./usePerformanceData";

export function useGrowthData(period: string) {
  const [summary, setSummary] = useState<PortfolioEvolutionSummary | null>(null);
  const [history, setHistory] = useState<PortfolioEvolutionPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const perfRes = await fetchPerformanceDataShared();

        if (!mounted) return;

        if (perfRes) {
          setSummary({
            patrimonio_atual: String(perfRes.market_value),
            patrimonio_atual_value: Number(perfRes.market_value || 0),
            rentabilidade_acumulada: Number(perfRes.metrics?.cagr || 0),
            proventos_totais: Number(perfRes.metrics?.dividends_received || 0),
            compras_totais: Number(perfRes.cost_basis || 0),
            vendas_totais: 0,
            ibov_acumulado_pct: 0,
            cdi_acumulado_pct: 0,
            alpha_vs_ibov: Number(perfRes.metrics?.cagr || 0),
            alpha_vs_cdi: Number(perfRes.metrics?.cagr || 0)
          });
          setHistory([]); // History will be implemented when backend supports series
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

    return () => {
      mounted = false;
    };
  }, []);

  // Filter history based on period
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

  // Calculate milestones
  const milestones: { value: number; label: string; date: string }[] = [];
  if (history.length > 0) {
    const checkMilestone = (value: number, label: string) => {
      const point = history.find(p => p.patrimonio_value >= value);
      if (point) {
        milestones.push({ value, label, date: point.month });
        return true;
      }
      return false;
    };
    checkMilestone(10000, "Primeiros R$ 10k");
    checkMilestone(50000, "R$ 50k Acumulados");
    checkMilestone(100000, "R$ 100k Alcançados");
    
    let nextCheck = 150000;
    while (checkMilestone(nextCheck, `R$ ${nextCheck / 1000}k Alcançados`)) {
      nextCheck += 50000;
    }
  }

  let nextTarget = 10000;
  const pat = summary?.patrimonio_atual_value || 0;
  if (pat < 10000) nextTarget = 10000;
  else if (pat < 50000) nextTarget = 50000;
  else if (pat < 100000) nextTarget = 100000;
  else {
    nextTarget = Math.floor(pat / 50000) * 50000 + 50000;
  }

  return {
    summary,
    history: filteredHistory,
    milestones,
    nextTarget,
    isLoading,
    isError
  };
}
