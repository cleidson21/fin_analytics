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
        const [sumRes, histRes] = await Promise.all([
          fetchFromAPI<PortfolioEvolutionSummary>("/investments/evolution/summary"),
          fetchFromAPI<PortfolioEvolutionPoint[]>("/investments/evolution/history")
        ]);

        if (!mounted) return;

        if (sumRes && histRes) {
          setSummary(sumRes);
          setHistory(histRes);
        } else {
          setIsError(true);
        }
      } catch (err) {
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
      if (point) milestones.push({ value, label, date: point.month });
    };
    checkMilestone(10000, "Primeiros R$ 10k");
    checkMilestone(50000, "R$ 50k Acumulados");
    checkMilestone(100000, "R$ 100k Alcançados");
  }

  return {
    summary,
    history: filteredHistory,
    milestones,
    isLoading,
    isError
  };
}
