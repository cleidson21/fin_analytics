"use client";

import { useDividendsData } from "@/hooks/useDividendsData";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthSectionTitle } from "@/components/wealth/ui/WealthSectionTitle";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { Coins, Percent, TrendingUp, CalendarDays } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { DividendFlowChart } from "@/components/wealth/charts/DividendFlowChart";
import { DividendYoYChart } from "@/components/wealth/charts/DividendYoYChart";

export default function DividendsPage() {
  const { 
    history, yoyArray, availableYears, 
    totalDividends, average12m, yieldOnCost, ytdReceived,
    isLoading, isError 
  } = useDividendsData();

  // Create table data: reversed history
  const tableData = [...history].reverse();

  return (
    <div className="space-y-6">
      <WealthSectionTitle 
        title="Dividendos" 
        subtitle="Acompanhamento de renda passiva e reinvestimento acumulado." 
      />

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
          title="PROJEÇÃO ANUAL"
          value={isLoading ? "..." : formatCurrency(average12m * 12)}
          icon={TrendingUp}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
          sub={
            isLoading ? "" : (
              <div className="w-full mt-1">
                {/* Barra de progresso YTD */}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WealthChartCard title="Fluxo Mensal de Proventos" isLoading={isLoading} isError={isError} className="h-[350px]">
          <DividendFlowChart data={history} />
        </WealthChartCard>
        
        <WealthChartCard title="Crescimento Ano a Ano (YoY)" isLoading={isLoading} isError={isError} className="h-[350px]">
          <DividendYoYChart data={yoyArray} years={availableYears} />
        </WealthChartCard>
      </div>

      <WealthChartCard title="Histórico de Recebimentos" isLoading={isLoading} isError={isError}>
         <WealthTable
            data={tableData}
            columns={[
              { header: "Mês", accessorKey: "month", className: "text-white font-medium" },
              { header: "Total Recebido", cell: (item) => formatCurrency(item.amount_received_value), align: "right", className: "text-[#f5a623] font-medium" },
              { header: "Variação M/M", cell: (item) => {
                 // To find index we could do tableData.indexOf(item), but that's O(n).
                 // For now, let's just use it safely.
                 const index = tableData.indexOf(item);
                 const prev = tableData[index + 1];
                 if (!prev || prev.amount_received_value === 0) return "-";
                 const variation = ((item.amount_received_value - prev.amount_received_value) / prev.amount_received_value) * 100;
                 return (
                   <span className={variation >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}>
                     {variation >= 0 ? "+" : ""}{variation.toFixed(1)}%
                   </span>
                 );
              }, align: "right" }
            ]}
         />
      </WealthChartCard>

    </div>
  );
}
