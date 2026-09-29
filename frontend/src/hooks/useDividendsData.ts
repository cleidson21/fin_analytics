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

interface DividendHistoryResponse {
  data_pagamento: string | null;
  valor: number | string | null;
  tipo_evento: string | null;
  ticker: string | null;
  cotas?: number | string | null;
  valor_por_cota?: number | string | null;
  yoc?: number | string | null;
  dy?: number | string | null;
}

interface DividendSummaryResponse {
  current_wealth: number | string | null;
  accumulated_return_pct: number | string | null;
  total_dividends: number | string | null;
  total_invested: number | string | null;
}

interface DividendBreakdownResponse {
  ticker: string;
  total_received: number | string | null;
}

// Per-asset detail for a given month
export interface AssetMonthDetail {
  ticker: string;
  recebido: number;
  cotas: number;
  valor_por_cota: number;
  yoc: number | null;
  dy: number | null;
  tipo_evento: string;
}

// { "2024-06": [ { ticker, recebido, cotas, ... }, ... ] }
export type MonthlyAssetDetails = Record<string, AssetMonthDetail[]>;

// Simple amount-only map (kept for chart coloring)
export type MonthlyAssets = Record<string, Record<string, number>>;

export function useDividendsData() {
  const [history, setHistory] = useState<DividendHistory[]>([]);
  const [breakdown, setBreakdown] = useState<DividendBreakdown[]>([]);
  const [summary, setSummary] = useState<PortfolioEvolutionSummary | null>(null);
  const [monthlyAssets, setMonthlyAssets] = useState<MonthlyAssets>({});
  const [monthlyAssetDetails, setMonthlyAssetDetails] = useState<MonthlyAssetDetails>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const summaryRes = await fetchFromAPI<DividendSummaryResponse>("/investments/evolution/summary");
        const historyRes = await fetchFromAPI<DividendHistoryResponse[]>("/investments/dividends/history");
        const breakdownRes = await fetchFromAPI<DividendBreakdownResponse[]>("/investments/dividends/breakdown");

        if (!mounted) return;
        if (summaryRes) {
          const aggregated: Record<string, DividendHistory> = {};
          const assetsByMonth: MonthlyAssets = {};
          // month -> ticker -> accumulated detail
          const detailsByMonth: Record<string, Record<string, AssetMonthDetail>> = {};

          if (historyRes) {
            historyRes.forEach(d => {
              if (!d.data_pagamento) return;
              const month = d.data_pagamento.substring(0, 7);

              // Aggregate monthly totals
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

              // Per-asset amount map (for chart)
              if (d.ticker) {
                if (!assetsByMonth[month]) assetsByMonth[month] = {};
                assetsByMonth[month][d.ticker] = (assetsByMonth[month][d.ticker] || 0) + val;
              }

              // Per-asset full details (for table)
              if (d.ticker) {
                if (!detailsByMonth[month]) detailsByMonth[month] = {};
                const key = `${d.ticker}||${d.tipo_evento}`;
                if (!detailsByMonth[month][key]) {
                  detailsByMonth[month][key] = {
                    ticker: d.ticker,
                    recebido: 0,
                    cotas: Number(d.cotas || 0),
                    valor_por_cota: Number(d.valor_por_cota || 0),
                    yoc: d.yoc != null ? Number(d.yoc) : null,
                    dy: d.dy != null ? Number(d.dy) : null,
                    tipo_evento: d.tipo_evento || "",
                  };
                }
                detailsByMonth[month][key].recebido += val;
              }
            });
          }

          const sortedHistory = Object.values(aggregated).sort((a, b) => a.month.localeCompare(b.month));
          setHistory(sortedHistory);
          setMonthlyAssets(assetsByMonth);

          // Convert details to arrays, sorted by recebido desc
          const detailsResult: MonthlyAssetDetails = {};
          for (const [month, tickerMap] of Object.entries(detailsByMonth)) {
            detailsResult[month] = Object.values(tickerMap).sort((a, b) => b.recebido - a.recebido);
          }
          setMonthlyAssetDetails(detailsResult);

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

  let average12m = 0;
  if (history.length > 0) {
    const last12 = history.slice(Math.max(history.length - 12, 0));
    const sum12m = last12.reduce((acc, curr) => acc + (curr.amount_received_value || 0), 0);
    average12m = sum12m / (last12.length || 1);
  }

  const yieldOnCost = summary?.compras_totais && summary.compras_totais > 0
    ? (totalDividends / summary.compras_totais) * 100
    : 0;

  const currentYear = new Date().getFullYear().toString();
  const ytdReceived = history
    .filter((h) => h.month?.startsWith(currentYear))
    .reduce((acc, h) => acc + (h.amount_received_value || 0), 0);

  const yoyData: Record<string, Record<string, number | string>> = {};
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

  months.forEach(m => { yoyData[m] = { name: m }; });

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
    monthlyAssets,
    monthlyAssetDetails,
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
