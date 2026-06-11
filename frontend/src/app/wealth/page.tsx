"use client";

import { useGrowthData } from "@/hooks/useGrowthData";
import { useDividendsData } from "@/hooks/useDividendsData";
import { useAllocationData } from "@/hooks/useAllocationData";
import { useAlphaData } from "@/hooks/useAlphaData";
import { useWealthStore } from "@/hooks/useWealthStore";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthPeriodToggle } from "@/components/wealth/ui/WealthPeriodToggle";
import { Wallet, TrendingUp, PieChart, Coins, Activity, Target, ShieldAlert } from "lucide-react";
import { formatCurrency, cn, colorForValue, getScoreColor } from "@/lib/utils";
import Link from "next/link";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { PieChart as RechartsPie, Pie, Cell, ResponsiveContainer } from "recharts";
import { getSemanticColor } from "@/lib/colors";

export default function WealthHome() {
  const { period, setPeriod } = useWealthStore();
  
  const growth = useGrowthData(period);
  const dividends = useDividendsData();
  const allocation = useAllocationData();
  const alpha = useAlphaData(period);

  const isLoading = growth.isLoading || dividends.isLoading || allocation.isLoading || alpha.isLoading;

  const currentPatrimonio = growth.summary?.patrimonio_atual_value || 0;
  const growthAcc = growth.summary?.rentabilidade_acumulada || 0;
  const div12m = dividends.average12m;
  const divYield = dividends.yieldOnCost;
  const alphaVal = alpha.summary?.alpha_vs_ibov || 0;
  
  return (
    <div className="space-y-6">
      <div className="flex justify-end mb-4">
        <WealthPeriodToggle active={period} onChange={setPeriod} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link href="/wealth/patrimonio" className="block group">
          <WealthKpiCard
            title="Patrimônio Consolidado"
            value={isLoading ? "..." : formatCurrency(currentPatrimonio)}
            icon={Wallet}
            iconBgColor="bg-[#4ecf98]/10"
            iconColor="text-[#4ecf98]"
            sub={isLoading ? "" : `Crescimento: ${growthAcc >= 0 ? "+" : ""}${growthAcc.toFixed(2)}%`}
            subColor={growthAcc >= 0 ? "positive" : "negative"}
            className="group-hover:border-[#4ecf98]/30 transition-all"
          />
        </Link>

        <Link href="/wealth/dividends" className="block group">
          <WealthKpiCard
            title="Média Mensal (12m)"
            value={isLoading ? "..." : formatCurrency(div12m)}
            icon={Coins}
            iconBgColor="bg-[#f5a623]/10"
            iconColor="text-[#f5a623]"
            sub={isLoading ? "" : `Yield on Cost: ${divYield.toFixed(2)}%`}
            subColor="neutral"
            className="group-hover:border-[#f5a623]/30 transition-all"
          />
        </Link>

        <Link href="/wealth/evolution" className="block group">
          <WealthKpiCard
            title="Alpha vs IBOV"
            value={<span className={colorForValue(alphaVal)}>{isLoading ? "..." : `${alphaVal >= 0 ? "+" : ""}${alphaVal.toFixed(2)}%`}</span>}
            icon={Activity}
            iconBgColor={alphaVal >= 0 ? "bg-[#4ecf98]/10" : "bg-[#e97070]/10"}
            iconColor={alphaVal >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}
            sub={isLoading ? "" : <span className="text-[#7EB8F7]">IBOV: {alpha.summary?.ibov_acumulado_pct.toFixed(2)}%</span>}
            subType="text"
            className="group-hover:border-white/20 transition-all"
          />
        </Link>

        <Link href="/wealth/allocation" className="block group">
          <WealthKpiCard
            title="Score de Diversificação"
            value={<span className={getScoreColor(allocation.diversificationScore)}>{isLoading ? "..." : `${allocation.diversificationScore}/100`}</span>}
            icon={PieChart}
            iconBgColor="bg-[#7F77DD]/10"
            iconColor="text-[#7F77DD]"
            sub={isLoading ? "" : `${allocation.totalAssets} Ativos na Carteira`}
            subColor="neutral"
            className="group-hover:border-[#7F77DD]/30 transition-all"
          />
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <WealthChartCard title="Acesso Rápido" tableMode>
           <div className="flex flex-col gap-2">
             {[
               { href: "/wealth/patrimonio", icon: Wallet, label: "Patrimônio: Detalhes & Marcos", badge: "CRESCIMENTO", iconBg: "rgba(78,207,152,0.12)", iconColor: "#4ecf98", badgeColor: "#4ecf98", badgeBg: "rgba(78,207,152,0.1)" },
               { href: "/wealth/allocation", icon: PieChart, label: "Alocação: Concentração de Risco", badge: "RISCO", iconBg: "rgba(233,112,112,0.12)", iconColor: "#e97070", badgeColor: "#e97070", badgeBg: "rgba(233,112,112,0.1)" },
               { href: "/wealth/dividends", icon: Coins, label: "Dividendos: Fluxo Anual", badge: "PROVENTOS", iconBg: "rgba(245,166,35,0.12)", iconColor: "#f5a623", badgeColor: "#f5a623", badgeBg: "rgba(245,166,35,0.1)" },
               { href: "/wealth/evolution", icon: TrendingUp, label: "Evolução: Benchmarks & Alpha", badge: "ANÁLISE", iconBg: "rgba(127,119,221,0.12)", iconColor: "#7F77DD", badgeColor: "#7F77DD", badgeBg: "rgba(127,119,221,0.1)" },
             ].map((item) => (
               <Link
                 key={item.href}
                 href={item.href}
                 className="flex items-center justify-between gap-3 p-3 rounded-xl transition-colors"
                 style={{ background: "rgba(255,255,255,0.02)" }}
                 onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
                 onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.02)"; }}
               >
                 <div className="flex items-center gap-3 min-w-0">
                   {/* Icon-box colorido */}
                   <div
                     className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                     style={{ background: item.iconBg }}
                   >
                     <item.icon size={15} style={{ color: item.iconColor }} />
                   </div>
                   <span className="text-sm font-medium text-neutral-300 break-words">{item.label}</span>
                 </div>
                 {/* Badge colorido por categoria */}
                 <span
                   className="text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full flex-shrink-0 ml-2"
                   style={{ color: item.badgeColor, background: item.badgeBg }}
                 >
                   {item.badge}
                 </span>
               </Link>
             ))}
           </div>
        </WealthChartCard>
        
        <WealthChartCard title="Insight de Risco" className="min-h-[200px]">
          <div className="flex flex-col h-full justify-center p-6 bg-white/[0.01] rounded-xl border border-white/[0.02]">
            
            {/* Insight 1: Classe Dominante */}
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-[#7F77DD]" />
                  <h4 className="text-white font-medium text-sm">Classe Dominante</h4>
                </div>
                <p className="text-neutral-400 text-xs max-w-[200px]">
                  Sua carteira está concentrada em <span className="text-white font-semibold">{allocation.dominantClass.name}</span>, 
                  representando <span className="text-white">{allocation.dominantClass.percentage.toFixed(1)}%</span> do total.
                </p>
              </div>
              <div className="w-12 h-12 flex-shrink-0 relative">
                <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
                  <RechartsPie>
                    <Pie
                      data={[
                        { value: allocation.dominantClass.percentage, color: getSemanticColor(allocation.dominantClass.name) },
                        { value: 100 - allocation.dominantClass.percentage, color: "rgba(255,255,255,0.05)" }
                      ]}
                      cx="50%" cy="50%" innerRadius="70%" outerRadius="100%" dataKey="value" stroke="none"
                    >
                      <Cell fill={getSemanticColor(allocation.dominantClass.name)} />
                      <Cell fill="rgba(255,255,255,0.05)" />
                    </Pie>
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border-t border-white/[0.05] my-4" />

            {/* Insight 2: Concentração Top 5 */}
            <div className="flex flex-col">
              <div className="flex items-center gap-2 mb-1">
                <ShieldAlert className={cn("w-4 h-4", allocation.top5Concentration > 70 ? "text-[#e97070]" : allocation.top5Concentration > 50 ? "text-[#f5a623]" : "text-[#4ecf98]")} />
                <span className={cn("text-[10px] uppercase tracking-widest font-medium", allocation.top5Concentration > 70 ? "text-[#e97070]" : allocation.top5Concentration > 50 ? "text-[#f5a623]" : "text-[#4ecf98]")}>Concentração Top 5</span>
              </div>
              <div className="flex items-end gap-2 mb-1">
                <span className={cn("text-xl font-semibold", allocation.top5Concentration > 70 ? "text-[#e97070]" : allocation.top5Concentration > 50 ? "text-[#f5a623]" : "text-[#4ecf98]")}>
                  {allocation.top5Concentration.toFixed(1)}%
                </span>
                <span className="text-xs text-neutral-500 mb-1">das 5 maiores posições no patrimônio</span>
              </div>
              <div className="w-full bg-white/[0.05] rounded-full h-1 overflow-hidden mt-1 mb-3">
                <div 
                  className={cn("h-full", allocation.top5Concentration > 70 ? "bg-[#e97070]" : allocation.top5Concentration > 50 ? "bg-[#f5a623]" : "bg-[#4ecf98]")} 
                  style={{ width: `${allocation.top5Concentration}%` }} 
                />
              </div>
              <Link href="/wealth/allocation" className="text-xs text-neutral-500 hover:text-white transition-colors self-start">
                Ver análise de risco &rarr;
              </Link>
            </div>

          </div>
        </WealthChartCard>
      </div>

    </div>
  );
}
