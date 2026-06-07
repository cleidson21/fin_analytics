import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { DividendHistory } from "@/hooks/useDividendsData";
import { formatCurrency } from "@/lib/utils";
import { WealthTooltip } from "@/components/wealth/ui/WealthTooltip";

interface DividendFlowChartProps {
  data: DividendHistory[];
}

export function DividendFlowChart({ data }: DividendFlowChartProps) {
  if (!data || data.length === 0) return null;

  // Calcular média móvel de 3 meses
  const processedData = data.map((d, i) => {
    let sum = 0;
    let count = 0;
    for (let j = Math.max(0, i - 2); j <= i; j++) {
      sum += data[j].amount_received_value;
      count++;
    }
    return { ...d, movingAvg: sum / count };
  });

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <ComposedChart data={processedData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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
          stroke="#374151"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(val) => `R$${(val).toFixed(0)}`}
        />
        <Tooltip
          content={(props) => (
            <WealthTooltip
              {...props}
              nameMap={{ amount_dividend_value: "Dividendos", amount_jcp_value: "JCP", amount_rendimento_value: "Rendimentos", movingAvg: "Média 3M" }}
              colorMap={{ amount_dividend_value: "#f5a623", amount_jcp_value: "#e97070", amount_rendimento_value: "#4ecf98", movingAvg: "#7EB8F7" }}
              valueFormatter={(v) => formatCurrency(v)}
            />
          )}
        />

        <Bar
          dataKey="amount_rendimento_value"
          stackId="a"
          fill="url(#gradRendimento)"
          maxBarSize={40}
        />
        <Bar
          dataKey="amount_dividend_value"
          stackId="a"
          fill="url(#gradDividendos)"
          maxBarSize={40}
        />
        <Bar
          dataKey="amount_jcp_value"
          stackId="a"
          fill="url(#gradJcp)"
          radius={[4, 4, 0, 0]}
          maxBarSize={40}
        />
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
  );
}
