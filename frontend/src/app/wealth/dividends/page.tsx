"use client";

import { useDividendsData, DividendBreakdown } from "@/hooks/useDividendsData";
import Link from 'next/link';
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { Coins, Percent, TrendingUp, CalendarDays } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { DividendFlowChart } from "@/components/wealth/charts/DividendFlowChart";
import { DividendYoYChart } from "@/components/wealth/charts/DividendYoYChart";
import { DividendMonthTable } from "@/components/wealth/charts/DividendMonthTable";

export default function DividendsPage() {
  const {
    history, breakdown, monthlyAssets, monthlyAssetDetails, yoyArray, availableYears,
    totalDividends, average12m, yieldOnCost, ytdReceived,
    isLoading, isError
  } = useDividendsData();

  // Create table data: reversed history (most recent first)
  const tableData = [...history].reverse();

  return (
    <div className="space-y-6">

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard
          title="Média Mensal (12m)"
          value={isLoading ? "..." : formatCurrency(average12m)}
          icon={CalendarDays}
          iconBgColor="bg-[#f5a623]/10"
          iconColor="text-[#f5a623]"
        />
        <WealthKpiCard
          title="Yield on Cost"
          value={isLoading ? "..." : `${yieldOnCost.toFixed(2)}%`}
          icon={Percent}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="Total Acumulado"
          value={isLoading ? "..." : formatCurrency(totalDividends)}
          icon={Coins}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
        />
        <WealthKpiCard
          title="Projeção Anual"
          value={isLoading ? "..." : formatCurrency(average12m * 12)}
          icon={TrendingUp}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
          sub={
            isLoading ? "" : (
              <div className="w-full mt-1">
                <div className="w-full rounded-full overflow-hidden" style={{ height: "4px", background: "rgba(255,255,255,0.06)" }}>
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min((ytdReceived / (average12m * 12)) * 100, 100)}%`,
                      background: "#f5a623",
                    }}
                  />
                </div>
                <p className="text-[10px] text-neutral-500 mt-1.5">
                  {formatCurrency(ytdReceived)} recebido de {formatCurrency(average12m * 12)} projetados
                </p>
              </div>
            )
          }
          subType="text"
        />
      </div>

      {/* Fluxo Mensal — full row, overflow visible so popup is not clipped */}
      <WealthChartCard
        title="Fluxo Mensal de Proventos"
        isLoading={isLoading}
        isError={isError}
        flexMode
        className="min-h-[360px] overflow-visible"
      >
        <DividendFlowChart data={history} monthlyAssets={monthlyAssets} />
      </WealthChartCard>

      {/* YoY — full row, extra tall for year toggles + chart */}
      <WealthChartCard
        title="Crescimento Ano a Ano (YoY)"
        isLoading={isLoading}
        isError={isError}
        className="h-[400px]"
      >
        <DividendYoYChart data={yoyArray} years={availableYears} />
      </WealthChartCard>

      {/* Tabela de composição por mês */}
      <WealthChartCard title="Composição Mensal Detalhada" isLoading={isLoading} isError={isError} tableMode>
        <DividendMonthTable
          monthlyAssetDetails={monthlyAssetDetails}
          availableMonths={[...history].reverse().map(h => h.month)}
        />
      </WealthChartCard>

      {/* Tables row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <WealthChartCard title="Histórico de Recebimentos" isLoading={isLoading} isError={isError} tableMode>
          <WealthTable
            data={tableData}
            pageSize={10}
            columns={[
              { header: "Mês", accessorKey: "month", className: "text-white font-medium" },
              { header: "Total Recebido", cell: (item) => formatCurrency(item.amount_received_value), align: "right", className: "text-[#f5a623] font-medium" },
              {
                header: "Variação M/M", cell: (item) => {
                  const index = tableData.indexOf(item);
                  const prev = tableData[index + 1];
                  if (!prev || prev.amount_received_value === 0) return "-";
                  const variation = ((item.amount_received_value - prev.amount_received_value) / prev.amount_received_value) * 100;
                  return (
                    <span className={variation >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}>
                      {variation >= 0 ? "+" : ""}{variation.toFixed(1)}%
                    </span>
                  );
                }, align: "right"
              }
            ]}
          />
        </WealthChartCard>

        <WealthChartCard title="Maiores Pagadores Históricos" isLoading={isLoading} isError={isError} tableMode>
          <WealthTable
            data={breakdown}
            pageSize={10}
            columns={[
              {
                header: "Ativo",
                cell: (item: DividendBreakdown) => (
                  <Link href={`/wealth/asset/${item.ticker}`} className="text-[#4ecf98] hover:underline font-medium">
                    {item.ticker}
                  </Link>
                )
              },
              { header: "Pagamentos", accessorKey: "quantidade_eventos", align: "right" },
              { header: "Total Recebido", cell: (item) => formatCurrency(item.total_recebido_value), align: "right", className: "text-[#4ecf98] font-medium" },
              { header: "Participação", cell: (item) => totalDividends > 0 ? `${((item.total_recebido_value / totalDividends) * 100).toFixed(1)}%` : "0%", align: "right" },
            ]}
          />
        </WealthChartCard>
      </div>

    </div>
  );
}
