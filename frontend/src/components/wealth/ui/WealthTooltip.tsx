import { formatCurrency } from "@/lib/utils";
import type { TooltipContentProps } from "recharts";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";

interface WealthTooltipProps extends TooltipContentProps<ValueType, NameType> {
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
    <div className="min-w-40 rounded-xl border border-border bg-popover px-4 py-3 text-popover-foreground shadow-xl">
      {formattedLabel && (
        <p className="mb-2.5 border-b border-border pb-2 text-[11px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
          {formattedLabel}
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
        {payload.map((entry, i) => {
          if (entry.value === undefined || entry.value === null) return null;

          const dataKeyStr = String(entry.dataKey || "");
          const displayName = nameMap[dataKeyStr] || entry.name || dataKeyStr;
          const color = colorMap[dataKeyStr] || entry.color || entry.stroke || "var(--foreground)";
          const rawValue = Number(Array.isArray(entry.value) ? entry.value[0] : entry.value);

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
                <span className="text-xs text-muted-foreground">{displayName}</span>
              </div>
              <span
                style={{
                  color: isPercentage
                    ? isPositive ? "var(--financial-positive)" : "var(--financial-negative)"
                    : "var(--foreground)",
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
