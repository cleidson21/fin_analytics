import { cn } from "@/lib/utils";

interface WealthSectionTitleProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function WealthSectionTitle({ title, subtitle, className }: WealthSectionTitleProps) {
  return (
    <div className={cn("flex flex-col mb-6", className)}>
      <h1 className="text-2xl md:text-3xl font-semibold text-foreground tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
