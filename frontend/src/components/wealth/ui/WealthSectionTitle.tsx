import { cn } from "@/lib/utils";

interface WealthSectionTitleProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function WealthSectionTitle({ title, subtitle, className }: WealthSectionTitleProps) {
  return (
    <div className={cn("flex flex-col mb-6", className)}>
      <h1 className="text-2xl md:text-3xl font-semibold text-white tracking-tight">{title}</h1>
      {subtitle && <p className="text-sm text-neutral-400 mt-1">{subtitle}</p>}
    </div>
  );
}
