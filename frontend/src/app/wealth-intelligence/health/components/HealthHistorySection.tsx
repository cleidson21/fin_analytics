"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { HistoricalFinancialMetric } from "../types";
import { financialTone, formatCurrency, formatPercent, formatReferenceMonth } from "../formatters";
import { HealthPanel } from "./HealthPanel";

const HISTORY_PAGE_SIZE = 12;

const seriesLabels: Record<string, string> = {
  income: "Receitas",
  expense: "Despesas",
  net: "Fluxo líquido",
};

export function HealthHistorySection({ history }: { history: HistoricalFinancialMetric[] }) {
  const [pageFromLatest, setPageFromLatest] = useState(0);

  if (history.length === 0) {
    return (
      <HealthPanel title="Histórico financeiro">
        <div className="rounded-xl border border-dashed border-white/10 px-4 py-10 text-center text-sm text-zinc-500">
          Não há histórico para exibir.
        </div>
      </HealthPanel>
    );
  }

  const chartHistory = history.slice(-6);
  const pageCount = Math.max(1, Math.ceil(history.length / HISTORY_PAGE_SIZE));
  const currentPageFromLatest = Math.min(pageFromLatest, pageCount - 1);
  const tableEnd = history.length - currentPageFromLatest * HISTORY_PAGE_SIZE;
  const tableStart = Math.max(0, tableEnd - HISTORY_PAGE_SIZE);
  const tableHistory = history.slice(tableStart, tableEnd);
  const rangeStart = currentPageFromLatest * HISTORY_PAGE_SIZE + 1;
  const rangeEnd = Math.min((currentPageFromLatest + 1) * HISTORY_PAGE_SIZE, history.length);
  const hasOlderRecords = tableStart > 0;
  const hasNewerRecords = currentPageFromLatest > 0;
  const chartData = chartHistory.map((item) => ({
    referenceMonth: item.reference_month,
    income: Number(item.total_income),
    expense: Number(item.total_expense),
    net: Number(item.net_cashflow),
  }));

  return (
    <HealthPanel
      title="Histórico financeiro"
      action={
        <span className="rounded-full border border-sky-400/15 bg-sky-400/[0.07] px-2.5 py-1 text-[11px] font-medium text-sky-300">
          {chartHistory.length === 1 ? "Último mês" : `Últimos ${chartHistory.length} meses`}
        </span>
      }
    >
      <div
        className="h-[300px] w-full sm:h-[340px]"
        role="img"
        aria-label="Gráfico mensal de receitas, despesas e fluxo líquido"
      >
        <ResponsiveContainer
          width="100%"
          height="100%"
          minWidth={1}
          minHeight={1}
          initialDimension={{ width: 800, height: 340 }}
        >
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="referenceMonth"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickFormatter={(value: string) => formatReferenceMonth(value, true)}
              minTickGap={18}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickFormatter={(value: number) =>
                new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 }).format(value)
              }
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.025)" }}
              contentStyle={{
                background: "rgba(18,18,20,0.97)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "12px",
                boxShadow: "0 16px 40px rgba(0,0,0,0.35)",
              }}
              labelStyle={{ color: "#e4e4e7", marginBottom: 8 }}
              labelFormatter={(value) => formatReferenceMonth(String(value))}
              formatter={(value, name) => [formatCurrency(String(value)), seriesLabels[String(name)] ?? String(name)]}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ color: "#a1a1aa", fontSize: 12, paddingTop: 12 }}
              formatter={(value) => seriesLabels[value] ?? value}
            />
            <Bar dataKey="income" fill="#34d399" radius={[4, 4, 0, 0]} maxBarSize={24} />
            <Bar dataKey="expense" fill="#fb7185" radius={[4, 4, 0, 0]} maxBarSize={24} />
            <Bar dataKey="net" fill="#38bdf8" radius={[4, 4, 0, 0]} maxBarSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 overflow-x-auto rounded-xl border border-white/[0.06]">
        <table className="w-full min-w-[650px] text-left text-xs">
          <caption className="sr-only">Valores mensais exatos do histórico financeiro</caption>
          <thead className="bg-black/20">
            <tr>
              <th scope="col" className="px-4 py-3 font-semibold text-zinc-400">Mês</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold text-emerald-300/80">Receitas</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold text-rose-300/80">Despesas</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold text-sky-300/80">Fluxo líquido</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold text-violet-300/80">Taxa</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.05]">
            {tableHistory.map((item) => (
              <tr
                key={item.reference_month}
                className="text-zinc-300 odd:bg-white/[0.012] even:bg-white/[0.028] hover:bg-white/[0.045]"
              >
                <th scope="row" className="whitespace-nowrap px-4 py-2.5 font-semibold capitalize text-zinc-100">
                  {formatReferenceMonth(item.reference_month)}
                </th>
                <td className="px-4 py-2.5 text-right font-medium tabular-nums text-emerald-300/90">
                  {formatCurrency(item.total_income)}
                </td>
                <td className="px-4 py-2.5 text-right font-medium tabular-nums text-rose-300/90">
                  {formatCurrency(item.total_expense)}
                </td>
                <td className={`px-4 py-2.5 text-right font-semibold tabular-nums ${financialTone(item.net_cashflow)}`}>
                  {formatCurrency(item.net_cashflow)}
                </td>
                <td className={`px-4 py-2.5 text-right font-semibold tabular-nums ${
                  item.savings_rate === null ? "text-zinc-600" : financialTone(item.savings_rate)
                }`}>
                  {formatPercent(item.savings_rate)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {history.length > HISTORY_PAGE_SIZE ? (
        <nav aria-label="Paginação do histórico" className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => setPageFromLatest((page) => Math.min(page + 1, pageCount - 1))}
            disabled={!hasOlderRecords}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.035] px-3 text-xs font-medium text-zinc-300 transition hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-35"
          >
            <ChevronLeft aria-hidden="true" size={14} />
            Anteriores
          </button>
          <span className="text-xs tabular-nums text-zinc-500">{rangeStart}–{rangeEnd} de {history.length}</span>
          <button
            type="button"
            onClick={() => setPageFromLatest((page) => Math.max(0, page - 1))}
            disabled={!hasNewerRecords}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.035] px-3 text-xs font-medium text-zinc-300 transition hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-35"
          >
            Mais recentes
            <ChevronRight aria-hidden="true" size={14} />
          </button>
        </nav>
      ) : null}
    </HealthPanel>
  );
}
