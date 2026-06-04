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

interface CashflowBarChartProps {
  data: any[];
}

export function CashflowBarChart({ data }: CashflowBarChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="gradAportesCash" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4ecf98" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#4ecf98" stopOpacity={0.3} />
          </linearGradient>
          <linearGradient id="gradProventosCash" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f5a623" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#f5a623" stopOpacity={0.3} />
          </linearGradient>
          <linearGradient id="gradVendasCash" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e97070" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#e97070" stopOpacity={0.3} />
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
          tickFormatter={(val) => `R$${(val / 1000).toFixed(0)}k`}
        />
        <Tooltip
          content={(props) => (
            <WealthTooltip
              {...props}
              nameMap={{
                compras_value: "Aportes",
                vendas_value: "Retiradas",
                proventos_value: "Proventos",
              }}
              colorMap={{
                compras_value: "#4ecf98",
                vendas_value: "#e97070",
                proventos_value: "#f5a623",
              }}
              valueFormatter={(v) => formatCurrency(v)}
            />
          )}
        />
        <Legend
          verticalAlign="top"
          height={36}
          iconType="circle"
          wrapperStyle={{ fontSize: "11px", color: "#6b7280" }}
          formatter={(value) => {
            if (value === "compras_value") return "Aportes";
            if (value === "vendas_value") return "Retiradas";
            if (value === "proventos_value") return "Proventos";
            return value;
          }}
        />
        <Bar dataKey="compras_value" fill="url(#gradAportesCash)" radius={[3, 3, 0, 0]} stackId="a" />
        <Bar dataKey="proventos_value" fill="url(#gradProventosCash)" radius={[3, 3, 0, 0]} stackId="a" />
        <Bar dataKey="vendas_value" fill="url(#gradVendasCash)" radius={[3, 3, 0, 0]} stackId="b" />
      </BarChart>
    </ResponsiveContainer>
  );
}
