import { formatCurrency } from "@/lib/utils";
import { TooltipProps } from "recharts";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface WealthTooltipProps extends TooltipProps<any, any> {
  active?: boolean;
  payload?: readonly any[];
  label?: string | number;
  _labelFormatter?: (label: string) => string;
  valueFormatter?: (value: number, dataKey: string) => string;
  nameMap?: Record<string, string>;
  colorMap?: Record<string, string>;
}

const defaultLabelFormatter = (label: string): string => {
  if (!label) return label;
  // Format YYYY-MM to "Jan/25" style
  const parts = label.split("-");
  if (parts.length === 2) {
    const months = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
    const month = parseInt(parts[1], 10) - 1;
    return `${months[month]}/${parts[0].slice(2)}`;
  }
  return label;
};

export function WealthTooltip({
  active,
  payload,
  label,
  _labelFormatter,
  valueFormatter,
  nameMap = {},
  colorMap = {},
}: WealthTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const labelFmt = _labelFormatter ?? defaultLabelFormatter;
  const formattedLabel = label !== undefined ? labelFmt(String(label)) : "";

  return (
    <div
      style={{
        backgroundColor: "rgba(20,20,20,0.97)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "12px",
        padding: "12px 16px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
        minWidth: "160px",
        backdropFilter: "blur(12px)",
      }}
    >
      {formattedLabel && (
        <p
          style={{
            color: "#6b7280",
            fontSize: "11px",
            fontWeight: 500,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginBottom: "10px",
            paddingBottom: "8px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          {formattedLabel}
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
        {payload.map((entry: any, i: number) => {
          if (entry.value === undefined || entry.value === null) return null;

          const dataKeyStr = String(entry.dataKey || "");
          const displayName = nameMap[dataKeyStr] || entry.name || dataKeyStr;
          const color = colorMap[dataKeyStr] || entry.color || entry.stroke || "#fff";
          const rawValue = Number(entry.value);

          let displayValue: string;
          if (valueFormatter) {
            displayValue = valueFormatter(rawValue, dataKeyStr);
          } else if (Math.abs(rawValue) >= 100) {
            displayValue = formatCurrency(rawValue);
          } else {
            displayValue = `${rawValue >= 0 ? "+" : ""}${rawValue.toFixed(2)}%`;
          }

          const isPositive = rawValue >= 0;
          const isPercentage = !valueFormatter && Math.abs(rawValue) < 100;

          return (
            <div
              key={i}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: color,
                    flexShrink: 0,
                    boxShadow: `0 0 6px ${color}80`,
                  }}
                />
                <span style={{ color: "#9ca3af", fontSize: "12px" }}>{displayName}</span>
              </div>
              <span
                style={{
                  color: isPercentage
                    ? isPositive ? "#4ecf98" : "#e97070"
                    : "#ffffff",
                  fontSize: "13px",
                  fontWeight: 600,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {displayValue}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
