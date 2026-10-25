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
    <div className="h-80 rounded-xl border border-border bg-card p-4 sm:p-5">
      <p className="mb-4 text-sm font-semibold tracking-tight text-foreground/90">{title}</p>
      {children}
    </div>
  );
}

function ProjectionTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ProjectionChartPoint }> }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;

  return (
    <div className="min-w-48 rounded-xl border border-border bg-popover px-3.5 py-3 shadow-xl">
      <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground">{point.periodEndLabel}</p>
      <dl className="mt-2 space-y-1.5 text-xs">
        <div className="flex justify-between gap-4"><dt className="text-muted-foreground">Patrimônio</dt><dd className="font-medium text-violet-700 dark:text-violet-300">{formatBRLDecimalString(point.endingWealthText)}</dd></div>
        <div className="flex justify-between gap-4"><dt className="text-muted-foreground">Aportes</dt><dd className="text-sky-700 dark:text-sky-300">{formatBRLDecimalString(point.cumulativeContributionsText)}</dd></div>
        <div className="flex justify-between gap-4"><dt className="text-muted-foreground">Crescimento</dt><dd className="text-success-foreground">{formatBRLDecimalString(point.cumulativeGrowthText)}</dd></div>
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
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="periodEndLabel" stroke="var(--chart-axis)" fontSize={10} tickLine={false} axisLine={false} minTickGap={28} />
          <YAxis stroke="var(--chart-axis)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={chartCurrency} width={96} />
          <Tooltip content={<ProjectionTooltip />} cursor={{ stroke: "var(--chart-grid)", strokeDasharray: "3 3" }} />
          <Legend verticalAlign="top" align="left" iconType="circle" iconSize={7} wrapperStyle={{ fontSize: "11px", paddingBottom: "10px", color: "var(--chart-axis)" }} />
          {/* Target line: amber dashed — preserved exactly, approved by user */}
          {targetAmount ? <ReferenceLine y={decimalForChart(targetAmount)} stroke="var(--chart-4)" strokeDasharray="6 5" strokeOpacity={0.8} ifOverflow="extendDomain" /> : null}
          {/* Primary series: slightly more prominent; supporting series: quieter */}
          <Line type="linear" dataKey="endingWealth" name="Patrimônio projetado" stroke="var(--chart-3)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "var(--chart-3)" }} />
          <Line type="linear" dataKey="cumulativeContributions" name="Aportes acumulados" stroke="var(--chart-2)" strokeWidth={1.5} dot={false} />
          <Line type="linear" dataKey="cumulativeGrowth" name="Crescimento acumulado" stroke="var(--chart-1)" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

type ScenarioChartPoint = Record<string, number | string>;

// Comparison chart: reference = neutral zinc, compared scenarios = violet/sky/etc.
// Color order: first scenario pair is reference(zinc) + compared(violet), then sky for 3rd, etc.
const scenarioReferenceColor = "var(--chart-axis)";  // zinc — neutral, recedes
const scenarioComparedColors = ["var(--chart-3)", "var(--chart-2)", "var(--chart-1)", "var(--chart-4)"];

function scenarioName(entry: ScenarioComparisonEntry, index: number) {
  return entry.label?.trim() || `Cenário ${index + 1}`;
}

function ScenarioTooltip({ active, payload, entries }: { active?: boolean; payload?: Array<{ payload: ScenarioChartPoint }>; entries: ScenarioComparisonEntry[] }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;

  return (
    <div className="min-w-48 rounded-xl border border-border bg-popover px-3.5 py-3 shadow-xl">
      <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground">{typeof point.periodEndLabel === "string" ? point.periodEndLabel : "Período"}</p>
      <dl className="mt-2 space-y-1.5 text-xs">
        {entries.map((entry, index) => {
          const text = point[`${entry.scenario_id}Text`];
          return (
            <div key={entry.scenario_id} className="flex justify-between gap-4">
              <dt className="text-muted-foreground">{scenarioName(entry, index)}</dt>
              <dd className="font-medium text-foreground">{typeof text === "string" ? formatBRLDecimalString(text) : "—"}</dd>
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
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="periodEndLabel" stroke="var(--chart-axis)" fontSize={10} tickLine={false} axisLine={false} minTickGap={28} />
          <YAxis stroke="var(--chart-axis)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={chartCurrency} width={96} />
          <Tooltip content={<ScenarioTooltip entries={entries} />} cursor={{ stroke: "var(--chart-grid)", strokeDasharray: "3 3" }} />
          <Legend verticalAlign="top" align="left" iconType="circle" iconSize={7} wrapperStyle={{ fontSize: "11px", paddingBottom: "10px", color: "var(--chart-axis)" }} />
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
