"use client";

import { useState } from "react";
import Link from "next/link";
import { useAllocationData, PositionDetail } from "@/hooks/useAllocationData";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { PieChart, ShieldAlert, LayoutGrid, Target } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { AllocationTreemap } from "@/components/wealth/charts/AllocationTreemap";
import { AllocationDonut } from "@/components/wealth/charts/AllocationDonut";
import { DiversificationGauge } from "@/components/wealth/charts/DiversificationGauge";

// ── Classify ticker into asset class ──────────────────────────────────────────

const ASSET_LABEL_MAP: Record<string, string> = {
  "FIXED_INCOME": "Renda Fixa",
  "STOCK": "Ações",
  "FII": "FIIs",
  "ETF_GLOBAL": "ETFs Globais",
  "BDR": "BDRs",
  "CRYPTO": "Criptomoedas",
  "OTHER": "Outros",
  "Todos": "Todos"
};

const ASSET_COLOR_MAP: Record<string, string> = {
  "FIXED_INCOME": "#34D399", // Emerald 400 - Safe, steady
  "STOCK": "#60A5FA",        // Blue 400 - Sleek, professional
  "FII": "#FBBF24",          // Amber 400 - Real estate, yield
  "ETF_GLOBAL": "#FB7185",   // Rose 400 - International
  "BDR": "#A78BFA",          // Purple 400
  "CRYPTO": "#FB923C",       // Orange 400 - High risk
  "OTHER": "#94A3B8",        // Slate 400 - Neutral
  "Desconhecido": "#94A3B8",
  "N/A": "#94A3B8"
};

function getTickerColor(assetClass: string): string {
  return ASSET_COLOR_MAP[assetClass] || ASSET_COLOR_MAP["OTHER"];
}

function getTickerLabel(assetClass: string): string {
  return ASSET_LABEL_MAP[assetClass] || assetClass;
}

const FILTER_PILLS = [
  { label: "Todos", value: "Todos" },
  { label: "Renda Fixa", value: "FIXED_INCOME" },
  { label: "Ações", value: "STOCK" },
  { label: "FIIs", value: "FII" },
  { label: "BDRs", value: "BDR" },
  { label: "ETFs Globais", value: "ETF_GLOBAL" },
  { label: "Cripto", value: "CRYPTO" },
];

export default function AllocationPage() {
  const [activeFilter, setActiveFilter] = useState<string>("Todos");

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
    name: getTickerLabel(a.asset_class),
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

  const filterLabel = activeFilter === "Todos" ? "Top 5 Posições (Risco)" : `Top 5 — ${getTickerLabel(activeFilter)}`;



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
          value={isLoading ? "..." : getTickerLabel(dominantClass.name)}
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
                    <span className="text-[10px] px-1.5 py-0.5 rounded text-neutral-500 font-semibold uppercase tracking-wider" style={{ background: "rgba(255,255,255,0.05)" }}>
                      {getTickerLabel(p.asset_class)}
                    </span>
                  </div>
                  <span className="text-neutral-400">{formatCurrency(p.valor_atual_value)} ({p.peso_percentual_value.toFixed(2)}%)</span>
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
              { header: "Preço Médio", cell: (item: unknown) => formatCurrency((item as PositionDetail).preco_medio_value || 0), align: "right" },
              { header: "Valor Investido", cell: (item: unknown) => formatCurrency((item as PositionDetail).valor_investido_value || 0), align: "right" },
              { 
                header: "Valor Atual", 
                cell: (item: unknown) => {
                  const p = item as PositionDetail;
                  if (!p.has_market_value) return <span className="text-neutral-500 font-mono">-</span>;
                  return (
                    <div className="flex flex-col items-end gap-0.5 leading-tight">
                      <span>{formatCurrency(p.valor_atual_value)}</span>
                      {p.market_data_provider === "YFINANCE" && (
                        <span className="text-[9px] text-neutral-500 border border-white/5 bg-white/[0.03] px-1 rounded uppercase tracking-wider">
                          Mercado
                        </span>
                      )}
                    </div>
                  );
                }, 
                align: "right" 
              },
              { 
                header: "Diferença (R$)", 
                cell: (item: unknown) => {
                  const p = item as PositionDetail;
                  if (!p.has_market_value) return <span className="text-neutral-500 font-mono">-</span>;
                  const val = p.ganho_value || 0;
                  const sign = val > 0 ? "+" : "";
                  return `${sign}${formatCurrency(val)}`;
                }, 
                align: "right", 
                className: (item: unknown) => {
                  const p = item as PositionDetail;
                  if (!p.has_market_value) return "";
                  const val = p.ganho_value || 0;
                  return val === 0 ? "text-neutral-500 font-mono" : `${val > 0 ? "text-[#4ecf98]" : "text-[#e97070]"} font-mono`;
                }
              },
              { header: "%", cell: (item: unknown) => {
                 const typedItem = item as PositionDetail;
                 if (!typedItem.has_market_value || !typedItem.valor_investido_value) return <span className="text-neutral-500 font-mono">-</span>;
                 const diff = ((typedItem.ganho_value || 0) / typedItem.valor_investido_value) * 100;
                 if (diff === 0) return <span className="text-neutral-500 font-mono">0.00%</span>;
                 return (
                   <span className={`${diff > 0 ? "text-[#4ecf98]" : "text-[#e97070]"} font-mono`}>
                     {diff > 0 ? "+" : ""}{diff.toFixed(2)}%
                   </span>
                 );
              }, align: "right" },
              { header: "Peso", cell: (item: unknown) => `${((item as PositionDetail).peso_percentual_value || 0).toFixed(2)}%`, align: "right", className: "text-neutral-400 font-mono" },
            ]}
          />
        </WealthChartCard>
      </div>
    </div>
  );
}
