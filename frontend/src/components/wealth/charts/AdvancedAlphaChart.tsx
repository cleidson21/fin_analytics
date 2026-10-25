import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { WealthTooltip } from "@/components/wealth/ui/WealthTooltip";

interface AdvancedAlphaChartProps {
  data: Record<string, unknown>[];
  showCarteira: boolean;
  showIbov: boolean;
  showCdi: boolean;
  showIpca: boolean;
  showIfix: boolean;
  showSp500: boolean;
  showIdiv: boolean;
}

const NAME_MAP: Record<string, string> = {
  rebased_cart: "Carteira",
  rebased_ibov: "IBOV",
  rebased_cdi: "CDI",
  rebased_ipca: "IPCA",
  rebased_ifix: "IFIX",
  rebased_sp500: "S&P 500",
  rebased_idiv: "IDIV",
};

const COLOR_MAP: Record<string, string> = {
  rebased_cart: "#4ecf98",
  rebased_ibov: "#7EB8F7",
  rebased_cdi: "#f5a623",
  rebased_ipca: "#e97070",
  rebased_ifix: "#7F77DD",
  rebased_sp500: "#f08a5d",
  rebased_idiv: "#86e3ce",
};

export function AdvancedAlphaChart({ data, showCarteira, showIbov, showCdi, showIpca, showIfix, showSp500, showIdiv }: AdvancedAlphaChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          {/* Área fill abaixo da linha Carteira */}
          <linearGradient id="gradCarteira" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#4ecf98" stopOpacity={0.18} />
            <stop offset="70%" stopColor="#4ecf98" stopOpacity={0.04} />
            <stop offset="100%" stopColor="#4ecf98" stopOpacity={0} />
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
          stroke="var(--chart-axis)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(val) => `${val.toFixed(0)}%`}
        />

        <Tooltip
          content={(props) => (
            <WealthTooltip
              {...props}
              nameMap={NAME_MAP}
              colorMap={COLOR_MAP}
            />
          )}
        />

        <Legend
          verticalAlign="bottom"
          height={36}
          iconType="plainline"
          wrapperStyle={{ fontSize: "11px", color: "var(--muted-foreground)", marginTop: "10px" }}
          formatter={(value) => NAME_MAP[value] || value}
        />

        {/* Área preenchida da Carteira (principal) */}
        {showCarteira && (
          <Area
            type="monotone"
            dataKey="rebased_cart"
            stroke="#4ecf98"
            strokeWidth={2.5}
            fill="url(#gradCarteira)"
            fillOpacity={1}
            dot={false}
            activeDot={{ r: 5, fill: "#4ecf98", stroke: "#0f0f0f", strokeWidth: 2, style: { filter: "drop-shadow(0 0 6px #4ecf9880)" } }}
          />
        )}

        {/* Benchmarks como linhas sem fill */}
        {showIbov && (
          <Line
            type="monotone"
            dataKey="rebased_ibov"
            stroke="#7EB8F7"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: "#7EB8F7" }}
          />
        )}
        {showCdi && (
          <Line
            type="monotone"
            dataKey="rebased_cdi"
            stroke="#f5a623"
            strokeWidth={1.5}
            strokeDasharray="5 3"
            dot={false}
            activeDot={{ r: 4, fill: "#f5a623" }}
          />
        )}
        {showIpca && (
          <Line
            type="monotone"
            dataKey="rebased_ipca"
            stroke="#e97070"
            strokeWidth={1.5}
            strokeDasharray="2 4"
            dot={false}
            activeDot={{ r: 4, fill: "#e97070" }}
          />
        )}
        {showIfix && (
          <Line
            type="monotone"
            dataKey="rebased_ifix"
            stroke="#7F77DD"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: "#7F77DD" }}
          />
        )}
        {showSp500 && (
          <Line
            type="monotone"
            dataKey="rebased_sp500"
            stroke="#f08a5d"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: "#f08a5d" }}
          />
        )}
        {showIdiv && (
          <Line
            type="monotone"
            dataKey="rebased_idiv"
            stroke="#86e3ce"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: "#86e3ce" }}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
