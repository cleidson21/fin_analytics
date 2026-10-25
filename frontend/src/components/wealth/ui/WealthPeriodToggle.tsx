import { cn } from "@/lib/utils";

export type WealthPeriod = "3M" | "6M" | "1A" | "2A" | "ALL";

interface WealthPeriodToggleProps {
  active: WealthPeriod;
  onChange: (period: WealthPeriod) => void;
  className?: string;
}

const PERIODS: { label: string; value: WealthPeriod }[] = [
  { label: "3M", value: "3M" },
  { label: "6M", value: "6M" },
  { label: "1A", value: "1A" },
  { label: "2A", value: "2A" },
  { label: "Tudo", value: "ALL" },
];

export function WealthPeriodToggle({ active, onChange, className }: WealthPeriodToggleProps) {
  return (
    <div role="group" aria-label="Período do gráfico" className={cn("inline-flex overflow-hidden rounded-lg border border-border bg-muted/30", className)}>
      {PERIODS.map((period) => {
        const isActive = active === period.value;
        return (
          <button
            key={period.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(period.value)}
            className={cn(
              "min-h-9 border-r border-border px-3 py-1 text-xs font-medium transition-colors last:border-r-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring motion-reduce:transition-none",
              isActive 
                ? "bg-accent text-accent-foreground"
                : "bg-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {period.label}
          </button>
        );
      })}
    </div>
  );
}
