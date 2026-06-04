"use client";

import { useState } from "react";
import { useAlphaData } from "@/hooks/useAlphaData";
import { useWealthStore } from "@/hooks/useWealthStore";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthSectionTitle } from "@/components/wealth/ui/WealthSectionTitle";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthPeriodToggle } from "@/components/wealth/ui/WealthPeriodToggle";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { Activity, Target, TrendingUp, Coins } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { AdvancedAlphaChart } from "@/components/wealth/charts/AdvancedAlphaChart";
import { CashflowBarChart } from "@/components/wealth/charts/CashflowBarChart";

export default function EvolutionPage() {
  const { period, setPeriod } = useWealthStore();
  const { history, rawHistory, summary, isLoading, isError } = useAlphaData(period);

  const [showCarteira, setShowCarteira] = useState(true);
  const [showIbov, setShowIbov] = useState(true);
  const [showCdi, setShowCdi] = useState(false);
  const [showIpca, setShowIpca] = useState(false);

  const alphaIbov = summary?.alpha_vs_ibov || 0;
  const alphaCdi = summary?.alpha_vs_cdi || 0;
  const rentabTotal = summary?.rentabilidade_acumulada || 0;
  const proventosTotais = summary?.proventos_totais || 0;
  const dy = summary?.patrimonio_atual_value && summary.patrimonio_atual_value > 0 
    ? (proventosTotais / summary.patrimonio_atual_value) * 100 
    : 0;

  // We use reversed rawHistory for the table
  const tableData = [...rawHistory].reverse();

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <WealthSectionTitle 
          title="Evolução & Performance" 
          subtitle="Análise comparativa de performance e geração de alpha vs benchmarks." 
          className="mb-0"
        />
        <WealthPeriodToggle active={period} onChange={setPeriod} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard
          title="Alpha vs IBOV"
          value={isLoading ? "..." : `${alphaIbov >= 0 ? "+" : ""}${alphaIbov.toFixed(2)}%`}
          icon={Activity}
          iconBgColor={alphaIbov >= 0 ? "bg-[#4ecf98]/10" : "bg-[#e97070]/10"}
          iconColor={alphaIbov >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}
          sub={isLoading ? "" : `IBOV: ${summary?.ibov_acumulado_pct.toFixed(2)}%`}
          subType="badge"
          subColor="neutral"
        />
        <WealthKpiCard
          title="Alpha vs CDI"
          value={isLoading ? "..." : `${alphaCdi >= 0 ? "+" : ""}${alphaCdi.toFixed(2)}%`}
          icon={Target}
          iconBgColor={alphaCdi >= 0 ? "bg-[#4ecf98]/10" : "bg-[#e97070]/10"}
          iconColor={alphaCdi >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}
          sub={isLoading ? "" : `CDI: ${summary?.cdi_acumulado_pct.toFixed(2)}%`}
          subType="badge"
          subColor="neutral"
        />
        <WealthKpiCard
          title="Rentabilidade Total"
          value={isLoading ? "..." : `${rentabTotal >= 0 ? "+" : ""}${rentabTotal.toFixed(2)}%`}
          icon={TrendingUp}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
        />
        <WealthKpiCard
          title="PROVENTOS NO PERÍODO"
          value={<span className="text-[#7EB8F7]">{isLoading ? "..." : formatCurrency(proventosTotais)}</span>}
          icon={Coins}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
          sub={isLoading ? "" : `DY: ${dy.toFixed(2)}%`}
          subType="badge"
          subColor="neutral"
        />
      </div>

      <div className="grid grid-cols-1 gap-6">
        <WealthChartCard 
          title="Rentabilidade Avançada vs Benchmarks (Rebased)" 
          isLoading={isLoading} 
          isError={isError} 
          className="h-[450px]"
          action={
            <div className="flex items-center gap-2 text-xs">
              <button onClick={() => setShowCarteira(!showCarteira)} className={cn("px-2 py-1 rounded transition-colors border", showCarteira ? "bg-[#4ecf98]/10 text-[#4ecf98] border-[#4ecf98]/25" : "bg-transparent text-neutral-600 border-transparent")}>Carteira</button>
              <button onClick={() => setShowIbov(!showIbov)} className={cn("px-2 py-1 rounded transition-colors border", showIbov ? "bg-[#7EB8F7]/10 text-[#7EB8F7] border-[#7EB8F7]/25" : "bg-transparent text-neutral-600 border-transparent")}>IBOV</button>
              <button onClick={() => setShowCdi(!showCdi)} className={cn("px-2 py-1 rounded transition-colors border", showCdi ? "bg-[#f5a623]/10 text-[#f5a623] border-[#f5a623]/25" : "bg-transparent text-neutral-600 border-transparent")}>CDI</button>
              <button onClick={() => setShowIpca(!showIpca)} className={cn("px-2 py-1 rounded transition-colors border", showIpca ? "bg-[#e97070]/10 text-[#e97070] border-[#e97070]/25" : "bg-transparent text-neutral-600 border-transparent")}>IPCA</button>
            </div>
          }
        >
          <AdvancedAlphaChart 
            data={history} 
            showCarteira={showCarteira} 
            showIbov={showIbov} 
            showCdi={showCdi} 
            showIpca={showIpca} 
          />
        </WealthChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WealthChartCard title="Fluxo de Caixa de Investimentos" isLoading={isLoading} isError={isError} className="h-[350px]">
          <CashflowBarChart data={rawHistory} />
        </WealthChartCard>
        
        <WealthChartCard title="Matriz Analítica Completa" isLoading={isLoading} isError={isError} className="h-[350px]">
          <WealthTable
            data={tableData}
            columns={[
              { header: "Mês", accessorKey: "month", className: "text-white font-medium" },
              { header: "Cart %", cell: (item) => `${item.rentabilidade_mensal_pct.toFixed(2)}%`, align: "right", className: (item) => item.rentabilidade_mensal_pct >= 0 ? "text-[#4ecf98] font-medium" : "text-[#e97070] font-medium" },
              { header: "IBOV %", cell: (item) => `${item.ibov_mensal_pct.toFixed(2)}%`, align: "right" },
              { header: "CDI %", cell: (item) => `${item.cdi_mensal_pct.toFixed(2)}%`, align: "right" },
              { header: "Aportes", cell: (item) => formatCurrency(item.compras_value), align: "right" },
              { header: "Vendas", cell: (item) => formatCurrency(item.vendas_value), align: "right" },
            ]}
          />
        </WealthChartCard>
      </div>

    </div>
  );
}
