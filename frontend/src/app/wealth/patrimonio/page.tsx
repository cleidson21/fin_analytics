"use client";

import { useGrowthData } from "@/hooks/useGrowthData";
import { useAllocationData } from "@/hooks/useAllocationData";
import { useWealthStore } from "@/hooks/useWealthStore";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthPeriodToggle } from "@/components/wealth/ui/WealthPeriodToggle";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { Wallet, TrendingUp, PiggyBank, LayoutGrid, Check, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { formatCurrency, colorForValue } from "@/lib/utils";
import { GrowthComposedChart } from "@/components/wealth/charts/GrowthComposedChart";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { DeltaBadge } from "@/components/ui/DeltaBadge";
import Link from "next/link";

export default function PatrimonioPage() {
  const { period, setPeriod } = useWealthStore();
  const { summary, history, milestones, nextTarget, isLoading: isGrowthLoading, isError } = useGrowthData(period);
  const { totalAssets, isLoading: isAllocLoading } = useAllocationData();

  const isLoading = isGrowthLoading || isAllocLoading;

  const currentPat = summary?.patrimonio_atual_value || 0;
  const growthAcc = summary?.rentabilidade_acumulada || 0;
  const totalInv = summary?.compras_totais || 0;
  const ganhoReal = currentPat - totalInv;
  const cdiAcc = summary?.cdi_acumulado_pct || 0;
  const alphaVsCdi = growthAcc - cdiAcc;

  const tableData = [...history].reverse();

  return (
    <div className="space-y-6">
      <div className="flex justify-end mb-4">
        <WealthPeriodToggle active={period} onChange={setPeriod} />
      </div>

      {/* KPI Cards secundários — menores, abaixo do hero */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <WealthKpiCard
          title="Patrimônio"
          value={isLoading ? "..." : formatCurrency(currentPat)}
          icon={Wallet}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
          sub={isLoading ? "" : <DeltaBadge value={growthAcc} />}
          subType="text"
        />
        <WealthKpiCard
          title="Total Aportado"
          value={isLoading ? "..." : formatCurrency(totalInv)}
          icon={PiggyBank}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
          sub={isLoading ? "" : <span className={`text-xs ${colorForValue(ganhoReal)}`}>Ganho real: {ganhoReal >= 0 ? "+" : ""}{formatCurrency(ganhoReal)}</span>}
          subType="text"
        />
        <WealthKpiCard
          title="Rentab. Acumulada"
          value={<span className={colorForValue(growthAcc)}>{isLoading ? "..." : `${growthAcc >= 0 ? "+" : ""}${growthAcc.toFixed(2)}%`}</span>}
          icon={TrendingUp}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
          sub={isLoading ? "" : <span className={`text-xs ${colorForValue(alphaVsCdi)}`}>vs CDI: {alphaVsCdi >= 0 ? "+" : ""}{alphaVsCdi.toFixed(2)}%</span>}
          subType="text"
        />
        <WealthKpiCard
          title="Nº de Ativos"
          value={isLoading ? "..." : totalAssets.toString()}
          icon={LayoutGrid}
          iconBgColor="bg-[#f5a623]/10"
          iconColor="text-[#f5a623]"
          sub={<Link href="/wealth/allocation" className="text-[#4ecf98]/70 hover:text-[#4ecf98] transition-colors">Ver distribuição →</Link>}
          subType="text"
        />
      </div>

      {/* Gráfico principal + Marcos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <WealthChartCard title="Patrimônio vs Aportes" isLoading={isLoading} isError={isError} className="h-[400px]">
            <GrowthComposedChart data={history} />
          </WealthChartCard>
        </div>
        <div className="flex flex-col gap-6">
          <WealthChartCard title="Marcos Patrimoniais" isLoading={isLoading} isError={isError} className="flex-1">
            <div className="relative flex flex-col gap-0 mt-4 pl-[11px]">
              <div className="absolute left-[11px] top-0 bottom-0 w-px bg-white/[0.06]" />

              {milestones.length === 0 ? (
                <p className="text-sm text-neutral-500 pl-6">Nenhum marco atingido no período.</p>
              ) : (
                milestones.map((m, i) => {
                  const [y, mm] = m.date.split("-");
                  const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
                  const dateStr = `${monthNames[parseInt(mm, 10)-1]}/${y}`;
                  return (
                    <div key={i} className="flex items-center gap-4 relative py-3 pl-6">
                      <div className="absolute left-[-11px] w-[22px] h-[22px] rounded-full bg-[#4ecf98]/15 border border-[#4ecf98]/40 flex items-center justify-center">
                        <Check className="w-2.5 h-2.5 text-[#4ecf98]" strokeWidth={3} />
                      </div>
                      <div>
                        <p className="text-[14px] font-medium text-white">{m.label}</p>
                        <p className="text-xs text-neutral-500">{dateStr}</p>
                      </div>
                    </div>
                  );
                })
              )}

              {currentPat > 0 && (
                <div className="flex items-center gap-4 relative py-3 pl-6 mt-2">
                  <div className="absolute left-[-11px] w-[22px] h-[22px] rounded-full bg-white/[0.04] border border-white/[0.08] border-dashed" />
                  <div className="flex-1">
                    <p className="text-[14px] font-medium text-[#4ecf98]">
                      Próximo Marco: R$ {nextTarget >= 1000 ? `${nextTarget / 1000}k` : nextTarget}
                    </p>
                    <div className="flex items-center gap-3 mt-1">
                      <div className="flex-1 bg-white/[0.05] rounded-full h-1 overflow-hidden">
                        <div className="bg-[#4ecf98]/50 h-full" style={{ width: `${Math.min((currentPat / nextTarget) * 100, 100)}%` }} />
                      </div>
                      <span className="text-xs text-[#4ecf98] whitespace-nowrap font-medium">{Math.min((currentPat / nextTarget * 100), 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </WealthChartCard>
        </div>
      </div>

      {/* Tabela */}
      <WealthChartCard title="Histórico de Crescimento Mensal" isLoading={isLoading} isError={isError} tableMode>
        <WealthTable
          data={tableData}
          pageSize={12}
          columns={[
            { header: "Mês", accessorKey: "month", className: "text-white font-medium" },
            { header: "Patrimônio", cell: (item) => formatCurrency(item.patrimonio_value), align: "right" },
            { header: "Aportes", cell: (item) => formatCurrency(item.compras_value), align: "right" },
            { header: "Proventos", cell: (item) => formatCurrency(item.proventos_value), align: "right", className: "text-[#f5a623]" },
            { header: "Rentabilidade", cell: (item) => `${item.rentabilidade_mensal_pct.toFixed(2)}%`, align: "right", className: (item) => item.rentabilidade_mensal_pct >= 0 ? "text-[#4ecf98] font-medium" : "text-[#e97070] font-medium" },
          ]}
        />
      </WealthChartCard>
    </div>
  );
}
