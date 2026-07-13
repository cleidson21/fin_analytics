"use client";

import { useState, useMemo } from "react";
import { usePositionsData } from "@/hooks/usePositionsData";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { AllocationDonut } from "@/components/wealth/charts/AllocationDonut";
import { formatCurrency, colorForValue } from "@/lib/utils";
import { Wallet, PiggyBank, TrendingUp, Search, Building2, Filter } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function PositionsPage() {
  const { data: positions, isLoading, isError } = usePositionsData();
  
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"Todas" | "Positiva" | "Negativa" | "Zerada">("Todas");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  // KPIs
  const { totalMarketValue, totalCostBasis, totalUnrealizedGain, overallReturn } = useMemo(() => {
    let mktVal = 0;
    let cost = 0;
    
    positions.forEach(p => {
      mktVal += p.market_value;
      cost += p.cost_basis;
    });

    const gain = mktVal - cost;
    const ret = cost > 0 ? (gain / cost) * 100 : 0;

    return {
      totalMarketValue: mktVal,
      totalCostBasis: cost,
      totalUnrealizedGain: gain,
      overallReturn: ret
    };
  }, [positions]);

  // Filters & Sorting
  const filteredPositions = useMemo(() => {
    let filtered = [...positions];
    
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(p => 
        p.ticker.toLowerCase().includes(lowerSearch) || 
        p.institution.toLowerCase().includes(lowerSearch)
      );
    }
    
    if (filterType === "Positiva") {
      filtered = filtered.filter(p => p.unrealized_gain > 0 && p.quantity > 0);
    } else if (filterType === "Negativa") {
      filtered = filtered.filter(p => p.unrealized_gain < 0 && p.quantity > 0);
    } else if (filterType === "Zerada") {
      filtered = filtered.filter(p => p.quantity <= 0);
    }
    
    // Default Sort: Maior Valor Mercado -> Menor
    return filtered.sort((a, b) => b.market_value - a.market_value);
  }, [positions, searchTerm, filterType]);

  // Chart 1: Top 10 Positions
  const top10Positions = useMemo(() => {
    return filteredPositions
      .filter(p => p.quantity > 0)
      .slice(0, 10)
      .map(p => ({
        name: p.ticker,
        value: p.market_value
      }));
  }, [filteredPositions]);

  // Chart 2: Distribution by Institution
  const institutionDonutData = useMemo(() => {
    const map = new Map<string, number>();
    filteredPositions.forEach(p => {
      if (p.quantity > 0) {
        map.set(p.institution, (map.get(p.institution) || 0) + p.market_value);
      }
    });
    
    const colors = ["#4ecf98", "#7F77DD", "#f5a623", "#7EB8F7", "#e97070", "#d1d5db"];
    return Array.from(map.entries())
      .map(([name, value], i) => ({
        name,
        value,
        color: colors[i % colors.length]
      }))
      .sort((a, b) => b.value - a.value);
  }, [filteredPositions]);

  // Custom Tooltip for Top 10 BarChart
  const CustomBarTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#141414]/95 border border-white/10 rounded-xl p-3 shadow-2xl backdrop-blur-xl">
          <p className="text-white font-medium mb-1">{payload[0].payload.name}</p>
          <p className="text-[#4ecf98] font-semibold">{formatCurrency(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      
      {/* Header / KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard
          title="Patrimônio (MTM)"
          value={isLoading ? "..." : formatCurrency(totalMarketValue)}
          icon={Wallet}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="Valor Investido"
          value={isLoading ? "..." : formatCurrency(totalCostBasis)}
          icon={PiggyBank}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
        />
        <WealthKpiCard
          title="Ganho Não Realizado"
          value={<span className={colorForValue(totalUnrealizedGain)}>{isLoading ? "..." : `${totalUnrealizedGain >= 0 ? "+" : ""}${formatCurrency(totalUnrealizedGain)}`}</span>}
          icon={TrendingUp}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
        />
        <WealthKpiCard
          title="Rentabilidade (MTM)"
          value={<span className={colorForValue(overallReturn)}>{isLoading ? "..." : `${overallReturn >= 0 ? "+" : ""}${overallReturn.toFixed(2)}%`}</span>}
          icon={TrendingUp}
          iconBgColor={overallReturn >= 0 ? "bg-[#4ecf98]/10" : "bg-[#e97070]/10"}
          iconColor={overallReturn >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WealthChartCard title="Top 10 Posições" isLoading={isLoading} isError={isError} className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
            <BarChart data={top10Positions} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fill: "#6b7280", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(val) => `R$ ${val / 1000}k`} tick={{ fill: "#6b7280", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomBarTooltip />} cursor={{ fill: "rgba(255,255,255,0.02)" }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {top10Positions.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill="#4ecf98" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </WealthChartCard>

        <WealthChartCard title="Distribuição por Instituição" isLoading={isLoading} isError={isError} className="h-[350px]">
           <div className="flex flex-col h-full">
            <div className="flex-1 min-h-0">
              <AllocationDonut data={institutionDonutData} />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 max-h-[80px] overflow-y-auto pr-1">
              {institutionDonutData.map((d, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
                  <span className="text-xs text-neutral-300 truncate">{d.name}</span>
                  <span className="text-xs text-neutral-500 ml-auto">
                    {totalMarketValue > 0 ? ((d.value / totalMarketValue) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </WealthChartCard>
      </div>

      {/* Table Section */}
      <div className="space-y-4">
        
        {/* Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white/[0.02] p-4 rounded-xl border border-white/[0.05]">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-[250px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input 
                type="text" 
                placeholder="Buscar por Ticker ou Instituição..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-neutral-600 focus:outline-none focus:border-[#4ecf98]/50 transition-colors"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-neutral-500 hidden sm:block mr-1" />
            {["Todas", "Positiva", "Negativa", "Zerada"].map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type as any)}
                className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                  filterType === type 
                    ? "bg-[#4ecf98]/10 text-[#4ecf98] border-[#4ecf98]/30" 
                    : "bg-transparent text-neutral-400 border-transparent hover:bg-white/5"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        {isError ? (
          <div className="p-8 text-center bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <p className="text-red-400 mb-2">Erro ao carregar as posições.</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-white/5 rounded-lg text-sm hover:bg-white/10 transition">Tentar novamente</button>
          </div>
        ) : (
          <WealthTable
            data={filteredPositions}
            pageSize={pageSize}
            isLoading={isLoading}
            emptyMessage={searchTerm ? "Nenhuma posição encontrada para sua busca." : "Nenhuma posição em carteira."}
            columns={[
              { 
                header: "Ativo", 
                accessorKey: "ticker",
                className: "font-semibold text-white" 
              },
              { 
                header: "Instituição", 
                cell: (p) => (
                  <div className="flex items-center gap-1.5 text-neutral-400">
                    <Building2 className="w-3.5 h-3.5 opacity-50" />
                    {p.institution}
                  </div>
                )
              },
              { 
                header: "Qtd", 
                cell: (p) => p.quantity.toString(),
                align: "right"
              },
              { 
                header: "Preço Médio", 
                cell: (p) => formatCurrency(p.average_cost),
                align: "right"
              },
              { 
                header: "Preço Atual", 
                cell: (p) => p.quantity > 0 ? formatCurrency(p.current_price) : "-",
                align: "right"
              },
              { 
                header: "Investido", 
                cell: (p) => formatCurrency(p.cost_basis),
                align: "right"
              },
              { 
                header: "Mercado", 
                cell: (p) => p.quantity > 0 ? formatCurrency(p.market_value) : "-",
                align: "right",
                className: "font-medium"
              },
              { 
                header: "Ganho (R$)", 
                cell: (p) => (
                  <span className={p.quantity > 0 ? colorForValue(p.unrealized_gain) : "text-neutral-600"}>
                    {p.quantity > 0 ? `${p.unrealized_gain >= 0 ? "+" : ""}${formatCurrency(p.unrealized_gain)}` : "-"}
                  </span>
                ),
                align: "right"
              },
              { 
                header: "Ganho (%)", 
                cell: (p) => (
                  <span className={p.quantity > 0 ? colorForValue(p.unrealized_gain_percent) : "text-neutral-600"}>
                    {p.quantity > 0 ? `${p.unrealized_gain_percent >= 0 ? "+" : ""}${p.unrealized_gain_percent.toFixed(2)}%` : "-"}
                  </span>
                ),
                align: "right",
                className: "font-medium"
              },
            ]}
          />
        )}
      </div>
    </div>
  );
}
