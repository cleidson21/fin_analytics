"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ReactNode } from "react";

import { formatBRDate, formatBRLDecimalString } from "@/lib/planningLocale";
import type { ForwardProjectionResponse, ScenarioComparisonEntry } from "@/lib/planning";

type ProjectionChartPoint = {
  period: number;
  periodEnd: string;
  periodEndLabel: string;
  endingWealth: number;
  endingWealthText: string;
  cumulativeContributions: number;
  cumulativeContributionsText: string;
  cumulativeGrowth: number;
  cumulativeGrowthText: string;
};

// Recharts accepts numbers only. This adapter is rendering-only: it neither
// updates Planning state nor participates in any financial calculation.
function decimalForChart(value: string): number {
  return Number(value);
}

function chartCurrency(value: unknown) {
  return typeof value === "number" ? formatBRLDecimalString(String(value)) : "—";
}

// Chart title uses analytic label style — not competing with hero
function ChartFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="h-80 rounded-xl border border-white/[0.06] bg-zinc-900/40 p-4 sm:p-5">
      <p className="mb-4 text-sm font-semibold tracking-tight text-zinc-300">{title}</p>
      {children}
    </div>
  );
}

function ProjectionTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ProjectionChartPoint }> }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;

  return (
    <div className="min-w-48 rounded-xl border border-white/[0.10] bg-zinc-950/95 px-3.5 py-3 shadow-xl">
      <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-zinc-500">{point.periodEndLabel}</p>
      <dl className="mt-2 space-y-1.5 text-xs">
        <div className="flex justify-between gap-4"><dt className="text-zinc-600">Patrimônio</dt><dd className="font-medium text-violet-200">{formatBRLDecimalString(point.endingWealthText)}</dd></div>
        <div className="flex justify-between gap-4"><dt className="text-zinc-600">Aportes</dt><dd className="text-sky-200">{formatBRLDecimalString(point.cumulativeContributionsText)}</dd></div>
        <div className="flex justify-between gap-4"><dt className="text-zinc-600">Crescimento</dt><dd className="text-emerald-200">{formatBRLDecimalString(point.cumulativeGrowthText)}</dd></div>
      </dl>
    </div>
  );
}

export function ProjectionChart({ result, targetAmount }: { result: ForwardProjectionResponse; targetAmount?: string | null }) {
  const data: ProjectionChartPoint[] = result.periods.map((period) => ({
    period: period.period,
    periodEnd: period.period_end,
    periodEndLabel: formatBRDate(period.period_end),
    endingWealth: decimalForChart(period.ending_wealth),
    endingWealthText: period.ending_wealth,
    cumulativeContributions: decimalForChart(period.cumulative_contributions),
    cumulativeContributionsText: period.cumulative_contributions,
    cumulativeGrowth: decimalForChart(period.cumulative_projected_growth),
    cumulativeGrowthText: period.cumulative_projected_growth,
  }));

  if (data.length === 0) return null;

  return (
    <ChartFrame title="Trajetória projetada">
      <ResponsiveContainer width="100%" height="90%" minWidth={1}>
        <LineChart data={data} margin={{ top: 10, right: 12, left: 6, bottom: 0 }}>
          {/* Grid: very low opacity — orient without competing */}
          <CartesianGrid stroke="rgba(255,255,255,0.14)" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="periodEndLabel" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} minTickGap={28} />
          <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={chartCurrency} width={96} />
          <Tooltip content={<ProjectionTooltip />} cursor={{ stroke: "rgba(255,255,255,0.10)", strokeDasharray: "3 3" }} />
          <Legend verticalAlign="top" align="left" iconType="circle" iconSize={7} wrapperStyle={{ fontSize: "11px", paddingBottom: "10px", color: "#71717a" }} />
          {/* Target line: amber dashed — preserved exactly, approved by user */}
          {targetAmount ? <ReferenceLine y={decimalForChart(targetAmount)} stroke="#fbbf24" strokeDasharray="6 5" strokeOpacity={0.7} ifOverflow="extendDomain" /> : null}
          {/* Primary series: slightly more prominent; supporting series: quieter */}
          <Line type="linear" dataKey="endingWealth" name="Patrimônio projetado" stroke="#a78bfa" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#a78bfa" }} />
          <Line type="linear" dataKey="cumulativeContributions" name="Aportes acumulados" stroke="#7dd3fc" strokeWidth={1.5} dot={false} />
          <Line type="linear" dataKey="cumulativeGrowth" name="Crescimento acumulado" stroke="#6ee7b7" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

type ScenarioChartPoint = Record<string, number | string>;

// Comparison chart: reference = neutral zinc, compared scenarios = violet/sky/etc.
// Color order: first scenario pair is reference(zinc) + compared(violet), then sky for 3rd, etc.
const scenarioReferenceColor = "#71717a";  // zinc — neutral, recedes
const scenarioComparedColors = ["#a78bfa", "#7dd3fc", "#6ee7b7", "#fcd34d"];  // violet, sky, emerald, amber

function scenarioName(entry: ScenarioComparisonEntry, index: number) {
  return entry.label?.trim() || `Cenário ${index + 1}`;
}

function ScenarioTooltip({ active, payload, entries }: { active?: boolean; payload?: Array<{ payload: ScenarioChartPoint }>; entries: ScenarioComparisonEntry[] }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;

  return (
    <div className="min-w-48 rounded-xl border border-white/[0.10] bg-zinc-950/95 px-3.5 py-3 shadow-xl">
      <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-zinc-500">{typeof point.periodEndLabel === "string" ? point.periodEndLabel : "Período"}</p>
      <dl className="mt-2 space-y-1.5 text-xs">
        {entries.map((entry, index) => {
          const text = point[`${entry.scenario_id}Text`];
          return (
            <div key={entry.scenario_id} className="flex justify-between gap-4">
              <dt className="text-zinc-600">{scenarioName(entry, index)}</dt>
              <dd className="font-medium text-zinc-200">{typeof text === "string" ? formatBRLDecimalString(text) : "—"}</dd>
            </div>
          );
        })}
      </dl>
    </div>
  );
}

export function ScenarioComparisonChart({ entries, referenceScenarioId }: { entries: ScenarioComparisonEntry[]; referenceScenarioId: string }) {
  const firstEntry = entries[0];
  if (!firstEntry) return null;

  const data: ScenarioChartPoint[] = firstEntry.projection_result.periods.map((period, index) => {
    const point: ScenarioChartPoint = {
      period: period.period,
      periodEndLabel: formatBRDate(period.period_end),
    };
    entries.forEach((entry) => {
      const certifiedPeriod = entry.projection_result.periods[index];
      if (certifiedPeriod) {
        point[entry.scenario_id] = decimalForChart(certifiedPeriod.ending_wealth);
        point[`${entry.scenario_id}Text`] = certifiedPeriod.ending_wealth;
      }
    });
    return point;
  });

  // Assign colors: reference gets neutral zinc, others get compared colors in order
  let comparedColorIndex = 0;
  const colorMap = new Map<string, string>();
  entries.forEach((entry) => {
    if (entry.scenario_id === referenceScenarioId) {
      colorMap.set(entry.scenario_id, scenarioReferenceColor);
    } else {
      colorMap.set(entry.scenario_id, scenarioComparedColors[comparedColorIndex % scenarioComparedColors.length] ?? scenarioComparedColors[0]!);
      comparedColorIndex++;
    }
  });

  return (
    <ChartFrame title="Trajetórias por cenário">
      <ResponsiveContainer width="100%" height="90%" minWidth={1}>
        <LineChart data={data} margin={{ top: 10, right: 12, left: 6, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.14)" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="periodEndLabel" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} minTickGap={28} />
          <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={chartCurrency} width={96} />
          <Tooltip content={<ScenarioTooltip entries={entries} />} cursor={{ stroke: "rgba(255,255,255,0.10)", strokeDasharray: "3 3" }} />
          <Legend verticalAlign="top" align="left" iconType="circle" iconSize={7} wrapperStyle={{ fontSize: "11px", paddingBottom: "10px", color: "#71717a" }} />
          {entries.map((entry) => {
            const isReference = entry.scenario_id === referenceScenarioId;
            const color = colorMap.get(entry.scenario_id) ?? scenarioReferenceColor;
            return (
              <Line
                key={entry.scenario_id}
                type="linear"
                dataKey={entry.scenario_id}
                name={scenarioName(entry, entries.indexOf(entry))}
                stroke={color}
                // Reference: solid, slightly lighter weight (recedes but legible)
                // Compared: solid, slightly bolder (figure in figure/ground)
                strokeWidth={isReference ? 1.5 : 2}
                strokeDasharray={isReference ? "4 3" : undefined}
                dot={false}
                activeDot={{ r: 4, fill: color }}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
