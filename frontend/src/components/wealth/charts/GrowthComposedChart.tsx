import {
  ComposedChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import { PortfolioEvolutionPoint } from "@/hooks/useGrowthData";
import { formatCurrency } from "@/lib/utils";
import { WealthTooltip } from "@/components/wealth/ui/WealthTooltip";

interface GrowthComposedChartProps {
  data: PortfolioEvolutionPoint[];
}

export function GrowthComposedChart({ data }: GrowthComposedChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          {/* Gradiente principal da área de patrimônio */}
          <linearGradient id="gradPatrimonio" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4ecf98" stopOpacity={0.25} />
            <stop offset="60%" stopColor="#4ecf98" stopOpacity={0.06} />
            <stop offset="100%" stopColor="#4ecf98" stopOpacity={0} />
          </linearGradient>
          {/* Gradiente das barras de aportes */}
          <linearGradient id="gradAportes" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7EB8F7" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#7EB8F7" stopOpacity={0.15} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--chart-grid)" />
        <XAxis
          dataKey="month"
          stroke="var(--chart-axis)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          minTickGap={30}
          tickFormatter={(val) => {
            const [year, month] = val.split("-");
            const months = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
            return `${months[parseInt(month) - 1]}/${year.slice(2)}`;
          }}
        />
        <YAxis
          yAxisId="patrimonio"
          stroke="var(--chart-axis)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(val) => `R$${(val / 1000).toFixed(0)}k`}
        />
        {/* Eixo separado para aportes, escala própria */}
        <YAxis
          yAxisId="aportes"
          orientation="right"
          hide={true}
        />
        <Tooltip
          content={(props) => (
            <WealthTooltip
              {...props}
              nameMap={{ patrimonio_value: "Patrimônio", compras_value: "Aportes" }}
              colorMap={{ patrimonio_value: "#4ecf98", compras_value: "#7EB8F7" }}
              valueFormatter={(v) => formatCurrency(v)}
            />
          )}
        />

        {/* Barras de aportes com eixo Y próprio */}
        <Bar
          yAxisId="aportes"
          dataKey="compras_value"
          fill="url(#gradAportes)"
          radius={[3, 3, 0, 0]}
          barSize={18}
          name="Aportes"
        />

        {/* Área de preenchimento abaixo da linha principal */}
        <Area
          yAxisId="patrimonio"
          type="monotone"
          dataKey="patrimonio_value"
          stroke="none"
          fill="url(#gradPatrimonio)"
          fillOpacity={1}
          dot={false}
          activeDot={false}
        />

        {/* Linha principal do patrimônio */}
        <Line
          yAxisId="patrimonio"
          type="monotone"
          dataKey="patrimonio_value"
          stroke="#4ecf98"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 5, fill: "#4ecf98", stroke: "#0f0f0f", strokeWidth: 2, style: { filter: "drop-shadow(0 0 6px #4ecf9880)" } }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
