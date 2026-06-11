import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatCurrency } from "@/lib/utils";
import { WealthTooltip } from "@/components/wealth/ui/WealthTooltip";

interface DividendYoYChartProps {
  data: Record<string, unknown>[];
  years: string[];
}

const YEAR_COLORS = ["#f5a623", "#4ecf98", "#7EB8F7", "#7F77DD", "#e97070"];
// gradient IDs derived from color index
const YEAR_GRADS = ["gradYoY0", "gradYoY1", "gradYoY2", "gradYoY3", "gradYoY4"];

export function DividendYoYChart({ data, years }: DividendYoYChartProps) {
  if (!data || data.length === 0 || !years || years.length === 0) return null;

  const nameMap: Record<string, string> = {};
  years.forEach((y) => { nameMap[y] = y; });

  const colorMap: Record<string, string> = {};
  years.forEach((y, i) => { colorMap[y] = YEAR_COLORS[i % YEAR_COLORS.length]; });

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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
        <Legend
          verticalAlign="top"
          height={36}
          iconType="circle"
          wrapperStyle={{ fontSize: "11px", color: "#6b7280" }}
        />
        {years.map((year, i) => (
          <Bar
            key={year}
            dataKey={year}
            fill={`url(#${YEAR_GRADS[i % YEAR_GRADS.length]})`}
            radius={[3, 3, 0, 0]}
            opacity={i === years.length - 1 ? 1 : 0.55}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
