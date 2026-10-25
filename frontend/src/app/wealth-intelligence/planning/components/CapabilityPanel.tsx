import type { ReactNode } from "react";

type CapabilityPanelProps = {
  title: string;
  children: ReactNode;
};

export function CapabilityPanel({ title, children }: CapabilityPanelProps) {
  return (
    <section className="space-y-4 rounded-xl border border-border bg-muted/25 p-4 sm:p-5">
      <h2 className="sr-only">{title}</h2>
      {children}
    </section>
  );
}

export function CapabilityError({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  return (
    <section role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.055] p-4">
      <p className="text-sm text-destructive">{message}</p>
      <button type="button" onClick={onDismiss} className="rounded-lg border border-rose-300/20 px-3 py-1.5 text-xs font-semibold text-destructive hover:bg-rose-300/10">
        Fechar
      </button>
    </section>
  );
}

export function CapabilityEmpty({ children }: { children: ReactNode }) {
  return <p className="rounded-xl border border-dashed border-border bg-muted/25 p-4 text-sm text-muted-foreground">{children}</p>;
}

function ResultSkeleton() {
  return <div aria-hidden="true" className="space-y-4 rounded-xl border border-border bg-card p-5 motion-safe:animate-pulse motion-reduce:animate-none"><div className="h-3 w-36 rounded bg-muted/60" /><div className="h-10 w-3/5 rounded bg-muted/70" /><div className="grid gap-3 sm:grid-cols-3"><div className="h-14 rounded bg-muted/50" /><div className="h-14 rounded bg-muted/50" /><div className="h-14 rounded bg-muted/50" /></div><div className="h-56 rounded bg-muted/45" /></div>;
}

export function CapabilityResultState({ hasResult, loading, dirty, loadingLabel, empty, action, children }: { hasResult: boolean; loading: boolean; dirty: boolean; loadingLabel: string; empty: ReactNode; action?: ReactNode; children: ReactNode }) {
  if (!hasResult && loading) return <section className="mt-8" aria-live="polite"><p role="status" className="sr-only">{loadingLabel}</p><ResultSkeleton /></section>;
  if (!hasResult) return <div className="mt-5">{empty}</div>;
  return <section className="mt-6" aria-live="polite">{loading ? <p role="status" className="mb-3 text-xs text-muted-foreground">Atualizando resultado…</p> : null}{!loading && dirty ? <p className="mb-3 text-xs text-muted-foreground">Premissas alteradas · simule novamente.</p> : null}<div className={`transition-[opacity,transform] duration-200 ease-out motion-reduce:transform-none motion-reduce:transition-none ${loading || dirty ? "opacity-60" : "opacity-100"}`}>{children}</div>{!loading && !dirty && action ? <div className="mt-4 flex justify-end border-t border-border pt-4">{action}</div> : null}</section>;
}
