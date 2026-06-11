import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface WealthKpiCardProps {
  title: string;
  value: string | ReactNode;
  icon: LucideIcon;
  iconBgColor?: string;
  iconColor?: string;
  sub?: ReactNode;
  subType?: "badge" | "text";
  subColor?: "positive" | "negative" | "neutral";
  className?: string;
}

export function WealthKpiCard({
  title,
  value,
  icon: Icon,
  iconBgColor = "bg-white/5",
  iconColor = "text-white",
  sub,
  subType = "text",
  subColor = "neutral",
  className,
}: WealthKpiCardProps) {
  const badgeColors = {
    positive: { bg: "rgba(78,207,152,0.1)", color: "#4ecf98", border: "rgba(78,207,152,0.2)" },
    negative: { bg: "rgba(233,112,112,0.1)", color: "#e97070", border: "rgba(233,112,112,0.2)" },
    neutral:  { bg: "rgba(255,255,255,0.05)", color: "#9ca3af", border: "rgba(255,255,255,0.08)" },
  };

  const badge = badgeColors[subColor];

  return (
    <div
      className={cn("relative rounded-2xl p-5 transition-all duration-200 group", className)}
      style={{
        background: "rgba(26,26,26,0.9)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.border = "1px solid rgba(255,255,255,0.12)";
        (e.currentTarget as HTMLElement).style.background = "rgba(30,30,30,0.95)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.border = "1px solid rgba(255,255,255,0.07)";
        (e.currentTarget as HTMLElement).style.background = "rgba(26,26,26,0.9)";
      }}
    >
      {/* Icon Box */}
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-3 flex-shrink-0", iconBgColor)}>
        <Icon size={20} className={iconColor} />
      </div>

      {/* Label */}
      <h3 className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
        {title}
      </h3>

      {/* Value */}
      <div className="text-[20px] font-medium text-white tracking-tight leading-snug mb-1">
        {value}
      </div>

      {/* Sub */}
      {sub && (
        <div>
          {subType === "badge" ? (
            <span
              className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              style={{ background: badge.bg, color: badge.color, border: `1px solid ${badge.border}` }}
            >
              {sub}
            </span>
          ) : (
            <div className="text-xs text-neutral-500">{sub}</div>
          )}
        </div>
      )}
    </div>
  );
}
