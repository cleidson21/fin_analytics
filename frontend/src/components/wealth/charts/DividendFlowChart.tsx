"use client";

import { useState } from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { DividendHistory, MonthlyAssets } from "@/hooks/useDividendsData";
import { formatCurrency } from "@/lib/utils";
import { WealthTooltip } from "@/components/wealth/ui/WealthTooltip";
import { X } from "lucide-react";

interface DividendFlowChartProps {
  data: DividendHistory[];
  monthlyAssets?: MonthlyAssets;
}

const WINDOW_OPTIONS = [
  { label: "6m", value: 6 },
  { label: "12m", value: 12 },
  { label: "24m", value: 24 },
  { label: "Tudo", value: 0 },
];

const ASSET_COLORS = [
  "#f5a623", "#4ecf98", "#7EB8F7", "#b794f4", "#e97070",
  "#34d399", "#f687b3", "#fbbf24", "#60a5fa", "#a78bfa",
];

function formatMonth(val: string) {
  const [year, month] = val.split("-");
  const months = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
  return `${months[parseInt(month) - 1]}/${year.slice(2)}`;
}

export function DividendFlowChart({ data, monthlyAssets = {} }: DividendFlowChartProps) {
  const [windowMonths, setWindowMonths] = useState(12);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  if (!data || data.length === 0) return null;

  const windowedData = windowMonths === 0
    ? data
    : data.slice(Math.max(0, data.length - windowMonths));

  const processedData = windowedData.map((d, i) => {
    let sum = 0, count = 0;
    for (let j = Math.max(0, i - 2); j <= i; j++) {
      sum += windowedData[j].amount_received_value;
      count++;
    }
    return { ...d, movingAvg: sum / count };
  });

  // Build consistent color map for tickers
  const allTickers = Array.from(
    new Set(Object.values(monthlyAssets).flatMap(m => Object.keys(m)))
  ).sort();
  const tickerColorMap: Record<string, string> = {};
  allTickers.forEach((t, i) => {
    tickerColorMap[t] = ASSET_COLORS[i % ASSET_COLORS.length];
  });

  return (
    <div className="relative flex flex-col gap-3" style={{ minHeight: 320 }}>

      {/* Window selector */}
      <div className="flex items-center gap-1 self-end">
        {WINDOW_OPTIONS.map(opt => (
          <button
            key={opt.label}
            onClick={() => setWindowMonths(opt.value)}
            className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-colors ${
              windowMonths === opt.value
                ? "bg-[#f5a623]/20 text-[#f5a623] ring-1 ring-inset ring-[#f5a623]/30"
                : "text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.04]"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height={260} minWidth={1}>
          <ComposedChart
            data={processedData}
            margin={{ top: 4, right: 8, left: -10, bottom: 0 }}
            onClick={(event) => {
              const activeIndex = event.activeTooltipIndex;
              if (typeof activeIndex !== "number") return;
              const month = processedData[activeIndex]?.month;
              if (!month) return;
              setSelectedMonth(prev => prev === month ? null : month);
            }}
          >
            <defs>
              <linearGradient id="gradDividendos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f5a623" stopOpacity={0.85} />
                <stop offset="100%" stopColor="#f5a623" stopOpacity={0.35} />
              </linearGradient>
              <linearGradient id="gradJcp" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#e97070" stopOpacity={0.85} />
                <stop offset="100%" stopColor="#e97070" stopOpacity={0.35} />
              </linearGradient>
              <linearGradient id="gradRendimento" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4ecf98" stopOpacity={0.85} />
                <stop offset="100%" stopColor="#4ecf98" stopOpacity={0.35} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.04)" />
            <XAxis
              dataKey="month"
              stroke="#374151"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              minTickGap={28}
              tickFormatter={formatMonth}
            />
            <YAxis
              stroke="#374151"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `R$${(val).toFixed(0)}`}
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              content={(props) => (
                <WealthTooltip
                  {...props}
                  nameMap={{ amount_dividend_value: "Dividendos", amount_jcp_value: "JCP", amount_rendimento_value: "Rendimentos", movingAvg: "Média 3M" }}
                  colorMap={{ amount_dividend_value: "#f5a623", amount_jcp_value: "#e97070", amount_rendimento_value: "#4ecf98", movingAvg: "#7EB8F7" }}
                  valueFormatter={(v) => formatCurrency(v)}
                />
              )}
            />

            <Bar dataKey="amount_rendimento_value" stackId="a" fill="url(#gradRendimento)" maxBarSize={36}>
              {processedData.map((entry) => (
                <Cell key={entry.month} cursor="pointer" />
              ))}
            </Bar>
            <Bar dataKey="amount_dividend_value" stackId="a" fill="url(#gradDividendos)" maxBarSize={36}>
              {processedData.map((entry) => (
                <Cell key={entry.month} cursor="pointer" />
              ))}
            </Bar>
            <Bar dataKey="amount_jcp_value" stackId="a" fill="url(#gradJcp)" radius={[4, 4, 0, 0]} maxBarSize={36}>
              {processedData.map((entry) => (
                <Cell key={entry.month} cursor="pointer" />
              ))}
            </Bar>
            <Line
              type="monotone"
              dataKey="movingAvg"
              stroke="#7EB8F7"
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 3"
              activeDot={{ r: 4, fill: "#7EB8F7", stroke: "#0f0f0f", strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Hint */}
      <p className="text-[10px] text-zinc-600 text-center -mt-1">
        Clique em uma barra para ver a composição por ativo
      </p>

      {selectedMonth && (
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3 text-xs">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-semibold text-zinc-200">Composição — {formatMonth(selectedMonth)}</span>
            <button
              type="button"
              onClick={() => setSelectedMonth(null)}
              aria-label="Fechar composição"
              className="rounded p-1 text-zinc-500 transition-colors hover:bg-white/[0.06] hover:text-zinc-200"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(monthlyAssets[selectedMonth] ?? {})
              .sort(([, amountA], [, amountB]) => amountB - amountA)
              .map(([ticker, amount]) => (
                <span key={ticker} className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.04] px-2 py-1 text-zinc-300">
                  <span className="h-2 w-2 rounded-full" style={{ background: tickerColorMap[ticker] }} />
                  {ticker}: {formatCurrency(amount)}
                </span>
              ))}
          </div>
        </div>
      )}

    </div>
  );
}
