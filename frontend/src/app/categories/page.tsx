"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Cell, Pie, PieChart } from "recharts";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { getCategoryColor } from "@/lib/colors";
import { formatCurrency } from "@/lib/utils";
import {
  addMonths,
  formatMonthLabel,
  getCurrentMonth,
  getMonthBounds,
} from "@/lib/period";

interface CategoryBreakdown {
  category: string;
  total: number;
}

function formatPct(value: number, total: number): string {
  if (total === 0) return "0%";
  return ((value / total) * 100).toFixed(1) + "%";
}

export default function CategoriesPage() {
  const router = useRouter();
  const [month, setMonth] = useState<string>(getCurrentMonth);
  const [data, setData] = useState<CategoryBreakdown[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async (m: string) => {
    setLoading(true);
    const result = await fetchFromAPI<CategoryBreakdown[]>(
      `/dashboard/categories?month=${m}`
    );
    setData(result ?? []);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData(month);
  }, [month, loadData]);

  const handlePrev = () => setMonth((m) => addMonths(m, -1));
  const handleNext = () => setMonth((m) => addMonths(m, +1));

  const totalGeral = data.reduce((sum, c) => sum + c.total, 0);
  const maxValue = data.length > 0 ? Math.max(...data.map((c) => c.total)) : 1;

  const handleCategoryClick = (category: string) => {
    const { startDate, endDate } = getMonthBounds(month);
    router.push(
      `/transactions?startDate=${startDate}&endDate=${endDate}&category=${encodeURIComponent(category)}`
    );
  };

  const chartData = data.map((c, i) => ({
    name: c.category,
    value: c.total,
    color: getCategoryColor(c.category, i),
  }));

  return (
    <PageLayout
      title="Categorias"
      subtitle={`Dados de referência: ${month}`}
      hideTitle={true}
    >
      {/* ── Seletor de mês ───────────────────────────────────────── */}
      <div className="mb-6 flex items-center justify-end">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-800 bg-[#1a1a1a] text-neutral-200 transition-colors hover:bg-neutral-800 hover:text-white"
            aria-label="Mês anterior"
          >
            <ChevronLeft size={16} className="text-neutral-200" />
          </button>
          <span className="min-w-[140px] text-center text-sm font-medium text-white">
            {formatMonthLabel(month)}
          </span>
          <button
            onClick={handleNext}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-800 bg-[#1a1a1a] text-neutral-200 transition-colors hover:bg-neutral-800 hover:text-white"
            aria-label="Próximo mês"
          >
            <ChevronRight size={16} className="text-neutral-200" />
          </button>
        </div>
      </div>

      {/* ── Hero: donut + total ───────────────────────────────────── */}
      <div className="mb-6 flex items-center gap-8 rounded-xl border border-neutral-800 bg-[#1a1a1a] p-6">
        <div className="flex-1">
          <p className="text-3xl font-semibold tracking-tight text-white">
            {loading ? "—" : formatCurrency(totalGeral)}
          </p>
          <p className="mt-1 text-sm text-neutral-400">
            gasto em {formatMonthLabel(month)}
          </p>
        </div>
        <div className="w-[100px] h-[100px] flex-shrink-0">
          {!loading && chartData.length > 0 && (
            <PieChart width={100} height={100}>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={31}
                outerRadius={50}
                paddingAngle={2}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
                strokeWidth={0}
              >
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          )}
        </div>
      </div>

      {/* ── Lista de categorias ───────────────────────────────────── */}
      {loading ? (
        <div className="flex items-center justify-center py-12 text-sm text-neutral-400">
          A carregar categorias…
        </div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center py-12 text-sm text-neutral-400">
          Sem dados para {formatMonthLabel(month)}.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {data.map((cat, i) => {
            const color = getCategoryColor(cat.category, i);
            const barWidth = maxValue > 0
              ? Math.round((cat.total / maxValue) * 100)
              : 0;
            const pct = formatPct(cat.total, totalGeral);

            return (
              <button
                key={cat.category}
                onClick={() => handleCategoryClick(cat.category)}
                className="group w-full rounded-xl border border-neutral-800 bg-[#1a1a1a] p-4 text-left transition-colors hover:bg-neutral-800/40"
              >
                <div className="flex items-center gap-3 mb-2.5">
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="flex-1 text-sm font-medium capitalize text-white">
                    {cat.category.toLowerCase().replace(/_/g, " ")}
                  </span>
                  <span className="text-sm font-medium text-white">
                    {formatCurrency(cat.total)}
                  </span>
                  <span className="min-w-[42px] text-right text-xs text-neutral-400">
                    {pct}
                  </span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-neutral-800">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${barWidth}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </PageLayout>
  );
}