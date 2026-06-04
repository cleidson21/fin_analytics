import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";
import { PortfolioEvolutionSummary } from "./useGrowthData";

export interface DividendHistory {
  month: string; // e.g. "2023-01"
  amount_received: string;
  amount_received_value: number;
}

export function useDividendsData() {
  const [history, setHistory] = useState<DividendHistory[]>([]);
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
          fetchFromAPI<DividendHistory[]>("/investments/dividends/history"),
          fetchFromAPI<PortfolioEvolutionSummary>("/investments/evolution/summary")
        ]);

        if (!mounted) return;
        if (histRes) {
          setHistory(histRes);
          setSummary(sumRes || null);
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
  const yoyData: Record<string, any> = {};
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
