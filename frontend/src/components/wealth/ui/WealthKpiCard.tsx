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
  iconBgColor = "bg-muted/40",
  iconColor = "text-foreground",
  sub,
  subType = "text",
  subColor = "neutral",
  className,
}: WealthKpiCardProps) {
  const badgeColors = {
    positive: "border-success/25 bg-success/10 text-success-foreground",
    negative: "border-destructive/25 bg-destructive/10 text-destructive",
    neutral: "border-border bg-muted text-muted-foreground",
  };

  const badge = badgeColors[subColor];

  return (
    <div
      className={cn("group relative rounded-2xl border border-border bg-card p-5 text-card-foreground shadow-sm transition-colors duration-200 hover:bg-accent/25 motion-reduce:transition-none", className)}
    >
      {/* Icon Box */}
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-3 flex-shrink-0", iconBgColor)}>
        <Icon size={20} className={iconColor} />
      </div>

      {/* Label */}
      <h3 className="mb-1 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
        {title}
      </h3>

      {/* Value */}
      <div className="text-[20px] font-medium text-foreground tracking-tight leading-snug mb-1">
        {value}
      </div>

      {/* Sub */}
      {sub && (
        <div>
          {subType === "badge" ? (
            <span
              className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium", badge)}
            >
              {sub}
            </span>
          ) : (
            <div className="text-xs text-muted-foreground">{sub}</div>
          )}
        </div>
      )}
    </div>
  );
}
