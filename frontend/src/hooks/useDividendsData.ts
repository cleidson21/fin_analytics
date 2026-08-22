import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";
import { PortfolioEvolutionSummary } from "./useGrowthData";

export interface DividendHistory {
  month: string; // e.g. "2023-01"
  amount_received: string;
  amount_received_value: number;
  amount_dividend_value?: number;
  amount_jcp_value?: number;
  amount_rendimento_value?: number;
}

export interface DividendBreakdown {
  ticker: string;
  total_recebido: string;
  total_recebido_value: number;
  quantidade_eventos: number;
  primeiro_recebimento: string;
  ultimo_recebimento: string;
}

import { PerformanceSummary } from "./usePerformanceData";

export function useDividendsData() {
  const [history, setHistory] = useState<DividendHistory[]>([]);
  const [breakdown, setBreakdown] = useState<DividendBreakdown[]>([]);
  const [summary, setSummary] = useState<PortfolioEvolutionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const summaryRes = await fetchFromAPI<any>("/investments/evolution/summary");

        const historyRes = await fetchFromAPI<any[]>("/investments/dividends/history");
        const breakdownRes = await fetchFromAPI<any[]>("/investments/dividends/breakdown");

        if (!mounted) return;
        if (summaryRes) {
          
          const aggregated: Record<string, DividendHistory> = {};
          if (historyRes) {
            historyRes.forEach(d => {
              if (!d.data_pagamento) return;
              const month = d.data_pagamento.substring(0, 7); // YYYY-MM
              if (!aggregated[month]) {
                aggregated[month] = {
                  month,
                  amount_received: "0",
                  amount_received_value: 0,
                  amount_dividend_value: 0,
                  amount_jcp_value: 0,
                  amount_rendimento_value: 0
                };
              }
              const val = Number(d.valor || 0);
              aggregated[month].amount_received_value += val;
              
              if (d.tipo_evento === "DIVIDENDO") aggregated[month].amount_dividend_value! += val;
              else if (d.tipo_evento === "JCP") aggregated[month].amount_jcp_value! += val;
              else aggregated[month].amount_rendimento_value! += val;
              
              aggregated[month].amount_received = String(aggregated[month].amount_received_value);
            });
          }

          const sortedHistory = Object.values(aggregated).sort((a, b) => a.month.localeCompare(b.month));
          setHistory(sortedHistory);
          
          setBreakdown((breakdownRes || []).map(b => ({
            ticker: b.ticker,
            total_recebido: String(b.total_received),
            total_recebido_value: Number(b.total_received || 0),
            quantidade_eventos: 1,
            primeiro_recebimento: "",
            ultimo_recebimento: ""
          })));

          setSummary({
            patrimonio_atual: String(summaryRes.current_wealth || 0),
            patrimonio_atual_value: Number(summaryRes.current_wealth || 0),
            rentabilidade_acumulada: Number(summaryRes.accumulated_return_pct || 0),
            proventos_totais: Number(summaryRes.total_dividends || 0),
            compras_totais: Number(summaryRes.total_invested || 0),
            vendas_totais: 0,
            ibov_acumulado_pct: 0,
            cdi_acumulado_pct: 0,
            alpha_vs_ibov: 0,
            alpha_vs_cdi: 0
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

  const totalDividends = summary?.proventos_totais || 0;
  
  // Calculate 12-month average
  let average12m = 0;
  if (history.length > 0) {
    const last12 = history.slice(Math.max(history.length - 12, 0));
    const sum12m = last12.reduce((acc, curr) => acc + (curr.amount_received_value || 0), 0);
    average12m = sum12m / (last12.length || 1);
  }

  // Calculate yield on cost
  const yieldOnCost = summary?.compras_totais && summary.compras_totais > 0 
    ? (totalDividends / summary.compras_totais) * 100 
    : 0;

  // Calculate YTD received (current calendar year)
  const currentYear = new Date().getFullYear().toString();
  const ytdReceived = history
    .filter((h) => h.month?.startsWith(currentYear))
    .reduce((acc, h) => acc + (h.amount_received_value || 0), 0);

  // Transform for YoY Chart: group by month (Jan-Dec) and year
  // Result format: { name: 'Jan', '2023': 10, '2024': 15 }
  const yoyData: Record<string, Record<string, number | string>> = {};
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  
  months.forEach(m => {
    yoyData[m] = { name: m };
  });

  const availableYears = new Set<string>();

  history.forEach(item => {
    if (!item.month) return;
    const [year, monthStr] = item.month.split('-');
    if (year && monthStr) {
      const monthIdx = parseInt(monthStr, 10) - 1;
      const monthName = months[monthIdx];
      availableYears.add(year);
      yoyData[monthName][year] = item.amount_received_value;
    }
  });

  const yoyArray = months.map(m => yoyData[m]);

  return {
    history,
    breakdown,
    yoyArray,
    availableYears: Array.from(availableYears).sort(),
    totalDividends,
    average12m,
    yieldOnCost,
    ytdReceived,
    isLoading,
    isError
  };
}
