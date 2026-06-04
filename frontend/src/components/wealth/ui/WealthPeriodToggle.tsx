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
    <div className={cn("inline-flex bg-white/[0.02] border border-white/[0.07] rounded-lg overflow-hidden", className)}>
      {PERIODS.map((period) => {
        const isActive = active === period.value;
        return (
          <button
            key={period.value}
            onClick={() => onChange(period.value)}
            className={cn(
              "px-3 py-1 text-xs font-medium transition-all duration-200 border-r border-white/[0.05] last:border-r-0",
              isActive 
                ? "bg-[#1f1f1f] text-[#4ecf98]" 
                : "bg-transparent text-neutral-600 hover:text-neutral-400"
            )}
          >
            {period.label}
          </button>
        );
      })}
    </div>
  );
}
