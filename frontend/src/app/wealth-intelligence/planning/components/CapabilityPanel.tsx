import type { ReactNode } from "react";

type CapabilityPanelProps = {
  title: string;
  children: ReactNode;
};

export function CapabilityPanel({ title, children }: CapabilityPanelProps) {
  return (
    <section className="space-y-5 rounded-xl border border-white/[0.06] bg-white/[0.015] p-5 sm:p-6">
      <h2 className="sr-only">{title}</h2>
      {children}
    </section>
  );
}

export function CapabilityError({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <section role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.055] p-4">
      <p className="text-sm text-rose-100">{message}</p>
      <button type="button" onClick={onDismiss} className="rounded-lg border border-rose-300/20 px-3 py-1.5 text-xs font-semibold text-rose-100 hover:bg-rose-300/10">
        Fechar
      </button>
    </section>
  );
}

export function CapabilityEmpty({ children }: { children: ReactNode }) {
  return <p className="rounded-xl border border-dashed border-white/[0.10] bg-white/[0.015] p-5 text-sm text-zinc-400">{children}</p>;
}

function ResultSkeleton() {
  return <div aria-hidden="true" className="space-y-4 rounded-xl border border-white/[0.06] bg-zinc-900/30 p-5 motion-safe:animate-pulse motion-reduce:animate-none"><div className="h-3 w-36 rounded bg-white/[0.08]" /><div className="h-10 w-3/5 rounded bg-white/[0.10]" /><div className="grid gap-3 sm:grid-cols-3"><div className="h-14 rounded bg-white/[0.06]" /><div className="h-14 rounded bg-white/[0.06]" /><div className="h-14 rounded bg-white/[0.06]" /></div><div className="h-56 rounded bg-white/[0.05]" /></div>;
}

export function CapabilityResultState({ hasResult, loading, dirty, loadingLabel, empty, children }: { hasResult: boolean; loading: boolean; dirty: boolean; loadingLabel: string; empty: ReactNode; children: ReactNode }) {
  if (!hasResult && loading) return <section className="mt-8" aria-live="polite"><p role="status" className="sr-only">{loadingLabel}</p><ResultSkeleton /></section>;
  if (!hasResult) return <div className="mt-8">{empty}</div>;
  return <section className="mt-8" aria-live="polite">{loading ? <p role="status" className="mb-3 text-xs text-zinc-400">Atualizando resultado…</p> : null}{!loading && dirty ? <p className="mb-3 text-xs text-zinc-400">Premissas alteradas · simule novamente.</p> : null}<div className={`transition-[opacity,transform] duration-200 ease-out motion-reduce:transform-none motion-reduce:transition-none ${loading || dirty ? "opacity-60" : "opacity-100"}`}>{children}</div></section>;
}
