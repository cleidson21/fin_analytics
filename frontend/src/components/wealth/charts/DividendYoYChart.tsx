"use client";

import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency } from "@/lib/utils";
import { WealthTooltip } from "@/components/wealth/ui/WealthTooltip";

interface DividendYoYChartProps {
  data: Record<string, unknown>[];
  years: string[];
}

const YEAR_COLORS = ["#f5a623", "#4ecf98", "#7EB8F7", "#b794f4", "#e97070", "#34d399", "#f687b3"];
const YEAR_GRADS = YEAR_COLORS.map((_, i) => `gradYoY${i}`);

export function DividendYoYChart({ data, years }: DividendYoYChartProps) {
  const [activeYears, setActiveYears] = useState<Set<string>>(new Set(years));
  const yearsKey = years.join(",");

  // Sync when years prop changes (on data load)
  useEffect(() => {
    setActiveYears(new Set(yearsKey ? yearsKey.split(",") : []));
  }, [yearsKey]);

  if (!data || data.length === 0 || !years || years.length === 0) return null;

  const nameMap: Record<string, string> = {};
  years.forEach((y) => { nameMap[y] = y; });

  const colorMap: Record<string, string> = {};
  years.forEach((y, i) => { colorMap[y] = YEAR_COLORS[i % YEAR_COLORS.length]; });

  function toggleYear(year: string) {
    setActiveYears(prev => {
      const next = new Set(prev);
      if (next.has(year)) {
        if (next.size > 1) next.delete(year); // keep at least one
      } else {
        next.add(year);
      }
      return next;
    });
  }

  const visibleYears = years.filter(y => activeYears.has(y));

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* Year toggles */}
      <div className="flex flex-wrap items-center gap-2">
        {years.map((year, i) => {
          const color = YEAR_COLORS[i % YEAR_COLORS.length];
          const isActive = activeYears.has(year);
          return (
            <button
              key={year}
              onClick={() => toggleYear(year)}
              className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-all duration-150 ${
                isActive
                  ? "ring-1 ring-inset"
                  : "opacity-35 grayscale"
              }`}
              style={
                isActive
                  ? {
                      color,
                      background: `${color}18`,
                      boxShadow: `0 0 0 1px ${color}35`,
                    }
                  : { color: "#6b7280", background: "rgba(255,255,255,0.03)" }
              }
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: isActive ? color : "#6b7280" }}
              />
              {year}
            </button>
          );
        })}
        <span className="ml-auto text-[10px] text-zinc-600">
          {visibleYears.length} de {years.length} anos visíveis
        </span>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0" style={{ minHeight: 260 }}>
        <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: -10, bottom: 0 }} barCategoryGap="20%">
            <defs>
              {YEAR_COLORS.map((color, i) => (
                <linearGradient key={i} id={YEAR_GRADS[i]} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.9} />
                  <stop offset="100%" stopColor={color} stopOpacity={0.35} />
                </linearGradient>
              ))}
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.04)" />
            <XAxis
              dataKey="name"
              stroke="#374151"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#374151"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `R$${(val / 1000).toFixed(0)}k`}
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              content={(props) => (
                <WealthTooltip
                  {...props}
                  nameMap={nameMap}
                  colorMap={colorMap}
                  valueFormatter={(v) => formatCurrency(v)}
                  _labelFormatter={(l) => `Mês: ${l}`}
                />
              )}
            />
            {years.map((year, i) =>
              activeYears.has(year) ? (
                <Bar
                  key={year}
                  dataKey={year}
                  fill={`url(#${YEAR_GRADS[i % YEAR_GRADS.length]})`}
                  radius={[3, 3, 0, 0]}
                  maxBarSize={28}
                />
              ) : null
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
