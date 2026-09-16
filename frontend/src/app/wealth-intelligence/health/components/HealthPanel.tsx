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
      className={`rounded-2xl border border-white/[0.08] bg-white/[0.035] p-4 shadow-xl shadow-black/10 sm:p-5 ${className}`}
    >
      <header className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-zinc-100 sm:text-lg">{title}</h2>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}
