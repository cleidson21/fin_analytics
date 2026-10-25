import type { ReactNode } from "react";

interface HealthPanelProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function HealthPanel({
  title,
  action,
  children,
  className = "",
}: HealthPanelProps) {
  return (
    <section
      className={`rounded-2xl border border-border bg-muted/35 p-4 shadow-xl shadow-black/10 ${className}`}
    >
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}
