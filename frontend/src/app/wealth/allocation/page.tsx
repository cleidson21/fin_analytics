"use client";

import { useState } from "react";
import Link from "next/link";
import { useAllocationData } from "@/hooks/useAllocationData";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthSectionTitle } from "@/components/wealth/ui/WealthSectionTitle";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { PieChart, ShieldAlert, LayoutGrid, Target } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { AllocationTreemap } from "@/components/wealth/charts/AllocationTreemap";
import { AllocationDonut } from "@/components/wealth/charts/AllocationDonut";
import { DiversificationGauge } from "@/components/wealth/charts/DiversificationGauge";

// ── Classify ticker into asset class ──────────────────────────────────────────
type AssetClass = "Todos" | "Renda Fixa" | "Fundos Imobiliários (FIIs)" | "Ações Brasil" | "ETFs Globais" | "Criptomoedas" | "Outros";

function getTickerColor(assetClass: string): string {
  if (assetClass === "Renda Fixa") return "#4ecf98";
  if (assetClass === "Fundos Imobiliários (FIIs)") return "#7F77DD";
  if (assetClass === "Ações Brasil") return "#7EB8F7";
  if (assetClass === "Criptomoedas") return "#e97070";
  return "#f5a623"; // ETFs Globais / Outros
}

const FILTER_PILLS: { label: string; value: AssetClass }[] = [
  { label: "Todos", value: "Todos" },
  { label: "Renda Fixa", value: "Renda Fixa" },
  { label: "FIIs", value: "Fundos Imobiliários (FIIs)" },
  { label: "Ações BR", value: "Ações Brasil" },
  { label: "ETFs Globais", value: "ETFs Globais" },
  { label: "Criptomoedas", value: "Criptomoedas" },
];

export default function AllocationPage() {
  const [activeFilter, setActiveFilter] = useState<AssetClass>("Todos");

  const {
    allocation, positions, top5Concentration,
    totalAssets, dominantClass, diversificationScore,
    isLoading, isError
  } = useAllocationData();

  const treemapData = positions.map((p) => ({
    name: p.ticker,
    size: p.valor_atual_value,
    fill: getTickerColor(p.asset_class),
    peso: p.peso_percentual_value
  }));

  // ── Donut Data ───────────────────────────────────────────────────────────────
  const donutData = allocation.map((a) => ({
    name: a.asset_class,
    value: a.current_total_value,
    color: getTickerColor(a.asset_class)
  }));

  const totalValue = positions.reduce((acc, p) => acc + p.valor_atual_value, 0);

  // ── Filtered positions for table ─────────────────────────────────────────────
  const filteredPositions = activeFilter === "Todos"
    ? positions
    : positions.filter((p) => p.asset_class === activeFilter);

  // ── Top 5 of filtered ────────────────────────────────────────────────────────
  const filteredTop5 = [...filteredPositions]
    .sort((a, b) => b.valor_atual_value - a.valor_atual_value)
    .slice(0, 5);

  const filterLabel = activeFilter === "Todos" ? "Top 5 Posições (Risco)" : `Top 5 — ${activeFilter}`;



  return (
    <div className="space-y-6">


      {/* KPI Cards — Score com Gauge embutido */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card especial: Score com Gauge visual */}
        <div
          className="rounded-2xl p-5 transition-all duration-200"
          style={{ background: "rgba(26,26,26,0.9)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="flex items-start justify-between">
            <div>
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center mb-3"
                style={{
                  background: diversificationScore >= 66
                    ? "rgba(78,207,152,0.12)"
                    : diversificationScore >= 41
                    ? "rgba(245,166,35,0.12)"
                    : "rgba(233,112,112,0.12)"
                }}
              >
                <Target
                  size={17}
                  style={{
                    color: diversificationScore >= 66 ? "#4ecf98"
                      : diversificationScore >= 41 ? "#f5a623"
                      : "#e97070"
                  }}
                />
              </div>
              <h3 className="text-[10px] font-medium uppercase tracking-[0.08em] text-neutral-500 mb-1">
                Score de Diversificação
              </h3>
            </div>
            {!isLoading && (
              <DiversificationGauge score={diversificationScore} />
            )}
          </div>
          {!isLoading && (
            <span
              className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium mt-1"
              style={{
                background: diversificationScore >= 66 ? "rgba(78,207,152,0.1)" : diversificationScore >= 41 ? "rgba(245,166,35,0.1)" : "rgba(233,112,112,0.1)",
                color: diversificationScore >= 66 ? "#4ecf98" : diversificationScore >= 41 ? "#f5a623" : "#e97070",
                border: `1px solid ${diversificationScore >= 66 ? "rgba(78,207,152,0.2)" : diversificationScore >= 41 ? "rgba(245,166,35,0.2)" : "rgba(233,112,112,0.2)"}`,
              }}
            >
              {diversificationScore >= 66 ? "Bem Diversificado" : diversificationScore >= 41 ? "Moderado" : "Atenção: Concentrado"}
            </span>
          )}
        </div>

        <WealthKpiCard
          title="Classe Dominante"
          value={isLoading ? "..." : dominantClass.name}
          icon={PieChart}
          iconBgColor="bg-[#7F77DD]/10"
          iconColor="text-[#7F77DD]"
          sub={isLoading ? "" : `${dominantClass.percentage.toFixed(1)}% do portfólio`}
          subType="text"
        />
        <WealthKpiCard
          title="Concentração Top 5"
          value={isLoading ? "..." : `${top5Concentration.toFixed(1)}%`}
          icon={ShieldAlert}
          iconBgColor="bg-[#e97070]/10"
          iconColor="text-[#e97070]"
          sub={top5Concentration > 50 ? "Risco Elevado" : "Nível Saudável"}
          subType="badge"
          subColor={top5Concentration > 50 ? "negative" : "positive"}
        />
        <WealthKpiCard
          title="Total de Ativos"
          value={isLoading ? "..." : `${totalAssets}`}
          icon={LayoutGrid}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
        />
      </div>

      {/* Filtro por classe de ativo */}
      <div className="flex items-center gap-2 flex-wrap">
        {FILTER_PILLS.map((pill) => {
          const isActive = activeFilter === pill.value;
          return (
            <button
              key={pill.value}
              onClick={() => setActiveFilter(pill.value)}
              className="text-xs font-medium px-3 py-1.5 rounded-lg transition-all duration-200"
              style={
                isActive
                  ? { background: "rgba(78,207,152,0.1)", color: "#4ecf98", border: "1px solid rgba(78,207,152,0.3)" }
                  : { background: "rgba(255,255,255,0.03)", color: "#6b7280", border: "1px solid rgba(255,255,255,0.06)" }
              }
            >
              {pill.label}
            </button>
          );
        })}
        {activeFilter !== "Todos" && (
          <span className="text-xs text-neutral-500 ml-2">
            {filteredPositions.length} posição{filteredPositions.length !== 1 ? "ões" : ""}
          </span>
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <WealthChartCard title="Alocação Macro" isLoading={isLoading} isError={isError} className="lg:col-span-1 h-[350px]">
          <div className="flex flex-col h-full">
            <div className="flex-1 min-h-0">
              <AllocationDonut data={donutData} />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 max-h-[120px] overflow-y-auto pr-1">
              {donutData.map((d, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
                  <span className="text-xs text-neutral-300 truncate">{d.name}</span>
                  <span className="text-xs text-neutral-500 ml-auto">
                    {totalValue > 0 ? ((d.value / totalValue) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </WealthChartCard>

        <WealthChartCard title="Posições por Ativo" isLoading={isLoading} isError={isError} className="lg:col-span-2 h-[350px]">
          <AllocationTreemap data={treemapData} />
        </WealthChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <WealthChartCard title={filterLabel} isLoading={isLoading} isError={isError} className="lg:col-span-1" tableMode>
          <div className="space-y-4 mt-2">
            {filteredTop5.map((p, i) => (
              <div key={i} className="flex flex-col gap-1">
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getTickerColor(p.asset_class) }} />
                    <Link href={`/wealth/asset/${p.ticker}`} className="font-medium text-[#4ecf98] hover:underline cursor-pointer">{p.ticker}</Link>
                    <span className="text-[10px] px-1.5 py-0.5 rounded text-neutral-500" style={{ background: "rgba(255,255,255,0.05)" }}>
                      {p.asset_class}
                    </span>
                  </div>
                  <span className="text-neutral-400">{formatCurrency(p.valor_atual_value)} ({p.peso_percentual})</span>
                </div>
                <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: p.peso_percentual,
                      backgroundColor: getTickerColor(p.asset_class),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </WealthChartCard>

        <WealthChartCard title="Lista Completa de Posições" isLoading={isLoading} isError={isError} className="lg:col-span-2" tableMode>
          <WealthTable
            data={filteredPositions}
            pageSize={10}
            columns={[
              { 
                header: "Ticker", 
                cell: (item: unknown) => {
                  const typedItem = item as { ticker: string };
                  return (
                    <Link href={`/wealth/asset/${typedItem.ticker}`} className="text-[#4ecf98] hover:underline font-medium">
                      {typedItem.ticker}
                    </Link>
                  );
                }
              },
              { header: "Qtd", accessorKey: "quantidade", align: "right" },
              { header: "Preço Médio", cell: (item: unknown) => formatCurrency((item as any).preco_medio_value || 0), align: "right" },
              { header: "Valor Investido", cell: (item: unknown) => formatCurrency((item as any).valor_investido_value || 0), align: "right" },
              { header: "Valor Atual", cell: (item: unknown) => formatCurrency((item as any).valor_atual_value || 0), align: "right" },
              { header: "Diferença (R$)", cell: (item: unknown) => (item as any).ganho, align: "right", className: (item: unknown) => ((item as any).ganho_value || 0) >= 0 ? "text-[#4ecf98]" : "text-[#e97070]" },
              { header: "Diferença (%)", cell: (item: unknown) => {
                 const typedItem = item as any;
                 if (!typedItem.valor_investido_value || typedItem.valor_investido_value === 0) return "-";
                 const diff = ((typedItem.ganho_value || 0) / typedItem.valor_investido_value) * 100;
                 return (
                   <span className={diff >= 0 ? "text-[#4ecf98]" : "text-[#e97070]"}>
                     {diff >= 0 ? "+" : ""}{diff.toFixed(2)}%
                   </span>
                 );
              }, align: "right" },
              { header: "Peso", accessorKey: "peso_percentual", align: "right" },
            ]}
          />
        </WealthChartCard>
      </div>
    </div>
  );
}
