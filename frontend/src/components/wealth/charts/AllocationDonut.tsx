import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { formatCurrency } from "@/lib/utils";

interface AllocationDonutProps {
  data: {
    name: string;
    value: number;
    color: string;
  }[];
}

// Custom tooltip inline para o donut (payload vem como entrada pelo Pie)
const DonutTooltip = ({ active, payload }: any) => {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  const total = payload[0].payload?.total || d.value;

  return (
    <div
      style={{
        backgroundColor: "rgba(20,20,20,0.97)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "12px",
        padding: "12px 16px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
        <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: d.color, boxShadow: `0 0 6px ${d.color}80` }} />
        <span style={{ color: "#e5e7eb", fontSize: "13px", fontWeight: 600 }}>{d.name}</span>
      </div>
      <p style={{ color: "#ffffff", fontSize: "15px", fontWeight: 700, margin: 0 }}>{formatCurrency(d.value)}</p>
    </div>
  );
};

export function AllocationDonut({ data }: AllocationDonutProps) {
  if (!data || data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius="62%"
          outerRadius="92%"
          paddingAngle={2}
          dataKey="value"
          stroke="none"
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.color}
              style={{ filter: `drop-shadow(0 0 4px ${entry.color}40)`, cursor: "pointer" }}
            />
          ))}
        </Pie>
        <Tooltip content={<DonutTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  );
}
