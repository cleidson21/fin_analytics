"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatCurrency } from "@/lib/utils";

interface AllocationData {
  asset_class: string;
  current_total: string;
}

// TODO: Numa fase posterior, migrar para variáveis CSS do Tailwind (ex: var(--chart-1))
const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899", "#64748b"];

export function AllocationChart({ data }: { data: AllocationData[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-sm text-zinc-400 backdrop-blur">
        Sem dados de investimentos.
      </div>
    );
  }

  const chartData = data.map((entry) => ({
    name: entry.asset_class,
    value: Number.parseFloat(entry.current_total),
  }));

  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
      <p className="text-sm text-zinc-400">Alocação de Ativos</p>

      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={70}
              outerRadius={110}
              paddingAngle={2}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => formatCurrency(Number(value))}
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #27272a",
                borderRadius: "8px",
                color: "#f4f4f5",
              }}
              itemStyle={{ color: "#f4f4f5" }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}