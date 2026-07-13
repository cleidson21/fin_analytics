"use client";

import { useMemo } from "react";
import { usePerformanceData } from "@/hooks/usePerformanceData";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { formatCurrency, colorForValue } from "@/lib/utils";
import { TrendingUp, Percent, Clock, Calendar, BarChart2, DollarSign, Wallet } from "lucide-react";

export default function PerformancePage() {
  const { data, isLoading, isError } = usePerformanceData();

  // Metrics for UI derived from data
  const m = data?.metrics;

  const tableData = useMemo(() => {
    if (!data || !m) return [];
    return [
      { metric: "Holding Days", value: `${data.holding_days} dias` },
      { metric: "Cost Basis", value: formatCurrency(data.cost_basis) },
      { metric: "Market Value", value: formatCurrency(data.market_value) },
      { metric: "Unrealized Gain", value: formatCurrency(m.unrealized_gain), color: colorForValue(m.unrealized_gain) },
      { metric: "Unrealized %", value: `${m.unrealized_return_pct.toFixed(2)}%`, color: colorForValue(m.unrealized_return_pct) },
      { metric: "Realized Gain", value: formatCurrency(m.realized_gain), color: colorForValue(m.realized_gain) },
      { metric: "Total Return (Absoluto)", value: formatCurrency(m.total_return), color: colorForValue(m.total_return) },
      { metric: "Total Return %", value: `${m.total_return_pct.toFixed(2)}%`, color: colorForValue(m.total_return_pct) },
      { metric: "CAGR", value: `${m.cagr.toFixed(2)}%`, color: colorForValue(m.cagr) },
      { metric: "TWR (Time-Weighted Return)", value: `${m.twr.toFixed(2)}%`, color: colorForValue(m.twr) },
      { metric: "MWR (Money-Weighted Return)", value: `${m.mwr.toFixed(2)}%`, color: colorForValue(m.mwr) },
      { metric: "Yield on Cost", value: `${m.yield_on_cost.toFixed(2)}%`, color: "text-[#f5a623]" },
      { metric: "Annualized Return", value: `${m.annualized_return_pct.toFixed(2)}%`, color: colorForValue(m.annualized_return_pct) },
      { metric: "Monthly Return", value: `${m.monthly_return_pct.toFixed(2)}%`, color: colorForValue(m.monthly_return_pct) },
      { metric: "Daily Return", value: `${m.daily_return_pct.toFixed(4)}%`, color: colorForValue(m.daily_return_pct) },
    ];
  }, [data, m]);

  return (
    <div className="space-y-6">
      
      {/* Primeira Seção: Rentabilidade Temporal */}
      <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider mb-2">Rentabilidade e Taxas (TWR, MWR, CAGR)</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <WealthKpiCard
          title="CAGR"
          value={<span className={colorForValue(m?.cagr || 0)}>{isLoading ? "..." : `${m?.cagr.toFixed(2)}%`}</span>}
          icon={TrendingUp}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
        />
        <WealthKpiCard
          title="TWR"
          value={<span className={colorForValue(m?.twr || 0)}>{isLoading ? "..." : `${m?.twr.toFixed(2)}%`}</span>}
          icon={BarChart2}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="MWR"
          value={<span className={colorForValue(m?.mwr || 0)}>{isLoading ? "..." : `${m?.mwr.toFixed(2)}%`}</span>}
          icon={Percent}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
        />
        <WealthKpiCard
          title="Yield on Cost"
          value={<span className="text-[#f5a623]">{isLoading ? "..." : `${m?.yield_on_cost.toFixed(2)}%`}</span>}
          icon={DollarSign}
          iconBgColor="bg-[#f5a623]/10"
          iconColor="text-[#f5a623]"
        />
        <WealthKpiCard
          title="Retorno Anual"
          value={<span className={colorForValue(m?.annualized_return_pct || 0)}>{isLoading ? "..." : `${m?.annualized_return_pct.toFixed(2)}%`}</span>}
          icon={Calendar}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="Retorno Mensal"
          value={<span className={colorForValue(m?.monthly_return_pct || 0)}>{isLoading ? "..." : `${m?.monthly_return_pct.toFixed(2)}%`}</span>}
          icon={Calendar}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="Retorno Diário"
          value={<span className={colorForValue(m?.daily_return_pct || 0)}>{isLoading ? "..." : `${m?.daily_return_pct.toFixed(4)}%`}</span>}
          icon={Clock}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
      </div>

      {/* Segunda Seção: Ganhos Absolutos */}
      <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider mt-8 mb-2">Ganhos Absolutos</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard
          title="Ganho Não Realizado"
          value={<span className={colorForValue(m?.unrealized_gain || 0)}>{isLoading ? "..." : formatCurrency(m?.unrealized_gain || 0)}</span>}
          icon={Wallet}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
        />
        <WealthKpiCard
          title="Ganho Realizado"
          value={<span className={colorForValue(m?.realized_gain || 0)}>{isLoading ? "..." : formatCurrency(m?.realized_gain || 0)}</span>}
          icon={Wallet}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
        />
        <WealthKpiCard
          title="Dividendos Recebidos"
          value={<span className="text-[#f5a623]">{isLoading ? "..." : formatCurrency(m?.dividends_received || 0)}</span>}
          icon={DollarSign}
          iconBgColor="bg-[#f5a623]/10"
          iconColor="text-[#f5a623]"
        />
        <WealthKpiCard
          title="Retorno Total"
          value={<span className={colorForValue(m?.total_return || 0)}>{isLoading ? "..." : formatCurrency(m?.total_return || 0)}</span>}
          icon={TrendingUp}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
      </div>

      {/* Terceira Seção: Gráfico */}
      <div className="grid grid-cols-1 gap-6">
        <WealthChartCard title="Performance Acumulada" isLoading={isLoading} isError={isError} className="h-[350px]">
          <div className="flex items-center justify-center h-full w-full opacity-50 flex-col">
            <BarChart2 className="w-12 h-12 text-neutral-600 mb-2" />
            <p className="text-neutral-500 text-sm">A série histórica do portfólio será processada nos próximos Gates.</p>
            <p className="text-neutral-600 text-xs mt-1">Consulte a visão temporal consolidada na aba Evolução.</p>
          </div>
        </WealthChartCard>
      </div>

      {/* Quarta Seção: Tabela */}
      <div className="space-y-4">
        {isError ? (
          <div className="p-8 text-center bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <p className="text-red-400 mb-2">Erro ao carregar os dados de performance.</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-white/5 rounded-lg text-sm hover:bg-white/10 transition">Tentar novamente</button>
          </div>
        ) : (
          <WealthChartCard title="Detalhamento Técnico de Performance" tableMode>
            <WealthTable
              data={tableData}
              isLoading={isLoading}
              emptyMessage="Nenhuma métrica computada."
              columns={[
                { 
                  header: "Métrica", 
                  accessorKey: "metric",
                  className: "font-medium text-white/90" 
                },
                { 
                  header: "Valor", 
                  align: "right",
                  className: (item) => `${item.color || "text-white"}` + " font-semibold font-mono",
                  cell: (item) => item.value
                }
              ]}
            />
          </WealthChartCard>
        )}
      </div>

    </div>
  );
}
