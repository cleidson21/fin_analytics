"use client";

import { useEffect, useMemo, useState } from "react";

import { InstallmentCard, type InstallmentItem } from "@/components/dashboard/InstallmentCard";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { getCurrentMonth } from "@/lib/period";
import { formatCurrency } from "@/lib/utils";

interface InstallmentsSummary {
  month: string;
  active_installments: number;
  finished_installments: number;
  global_estimated: number;
  global_paid: number;
  global_remaining: number;
  last_installment_date: string | null;
  items: InstallmentItem[];
}

type ActiveTab = "andamento" | "finalizadas";
type SortBy = "restantes" | "maior_valor" | "menor_valor";

function LoadingLine({ width = "w-full" }: { width?: string }) {
  return <div className={`h-5 ${width} animate-pulse rounded bg-white/[0.05]`} />;
}

function compareItems(sortBy: SortBy, a: InstallmentItem, b: InstallmentItem) {
  if (sortBy === "restantes") {
    const aRemainingCount = a.total_installments - a.current_installment;
    const bRemainingCount = b.total_installments - b.current_installment;
    return bRemainingCount - aRemainingCount;
  }

  if (sortBy === "maior_valor") {
    return b.installment_amount - a.installment_amount;
  }

  return a.installment_amount - b.installment_amount;
}

export default function InstallmentsPage() {
  const [summary, setSummary] = useState<InstallmentsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ActiveTab>("andamento");
  const [sortBy, setSortBy] = useState<SortBy>("restantes");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const month = useMemo(() => getCurrentMonth(), []);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      const payload = await fetchFromAPI<InstallmentsSummary>("/dashboard/installments");

      if (!active) {
        return;
      }

      setSummary(payload);
      setLoading(false);
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  const allItems = useMemo(() => summary?.items ?? [], [summary]);

  const activeItems = useMemo(
    () => allItems.filter((item) => item.current_installment < item.total_installments),
    [allItems]
  );

  const finishedItems = useMemo(
    () => allItems.filter((item) => item.current_installment >= item.total_installments),
    [allItems]
  );

  const cardTotals = useMemo(() => {
    const totalInstallments = activeItems.length;
    const totalRemaining = activeItems.reduce((acc, item) => acc + item.remaining, 0);
    const totalPaid = activeItems.reduce((acc, item) => acc + item.already_paid, 0);
    const totalEstimated = activeItems.reduce((acc, item) => acc + item.total_estimated, 0);
    return { totalInstallments, totalRemaining, totalPaid, totalEstimated };
  }, [activeItems]);

  const displayedItems = useMemo(() => {
    const base = activeTab === "andamento" ? activeItems : finishedItems;
    return base.slice().sort((a, b) => compareItems(sortBy, a, b));
  }, [activeItems, activeTab, finishedItems, sortBy]);

  // Auto-abre o primeiro card ao trocar de aba
  useEffect(() => {
    if (displayedItems.length > 0) {
      setExpandedId(displayedItems[0].base_name);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleToggle = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  // Progresso geral (activas)
  const globalProgress =
    cardTotals.totalEstimated > 0
      ? Math.min((cardTotals.totalPaid / cardTotals.totalEstimated) * 100, 100)
      : 0;

  return (
    <PageLayout title="Parcelamentos" subtitle={`Visão global do histórico de compras parceladas. Referência atual: ${month}.`} hideTitle={true}>

      {/* ── KPI Cards ──────────────────────────────────────────────── */}
      <section>
        {loading || !summary ? (
          <div className="grid gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <article key={`inst-card-loading-${index}`} className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <LoadingLine width="w-24" />
                <div className="mt-3">
                  <LoadingLine width="w-32" />
                </div>
              </article>
            ))}
          </div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <p className="text-xs uppercase tracking-widest text-neutral-500">Em andamento</p>
                <p className="mt-2 text-4xl font-semibold text-white">{cardTotals.totalInstallments}</p>
                <p className="text-sm text-neutral-400">compras parceladas</p>
              </article>

              <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <p className="text-xs uppercase tracking-widest text-neutral-500">Valor total (estimado)</p>
                <p className="mt-2 text-4xl font-semibold text-white">{formatCurrency(cardTotals.totalEstimated)}</p>
              </article>

              <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <p className="text-xs uppercase tracking-widest text-neutral-500">Já pago</p>
                <p className="mt-2 text-4xl font-semibold text-[#4ecf98]">{formatCurrency(cardTotals.totalPaid)}</p>
              </article>

              <article className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
                <p className="text-xs uppercase tracking-widest text-neutral-500">Restante</p>
                <p className="mt-2 text-4xl font-semibold text-[#f5a623]">{formatCurrency(cardTotals.totalRemaining)}</p>
              </article>
            </div>

            {/* Card de progresso geral */}
            <div className="mt-4 rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm text-neutral-400">Progresso geral</span>
                <span className="text-sm font-medium text-[#4ecf98]">{globalProgress.toFixed(0)}% pago</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#4ecf98] to-[#3bb882] transition-all duration-500"
                  style={{ width: `${globalProgress}%` }}
                />
              </div>
              <p className="mt-3 text-xs text-neutral-500">
                📅 Última parcela: {summary.last_installment_date ?? "-"}
              </p>
            </div>
          </>
        )}
      </section>

      {/* ── Lista ─────────────────────────────────────────────────── */}
      <section className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
        <div className="flex flex-col gap-3 border-b border-white/[0.05] pb-4 md:flex-row md:items-center md:justify-between">
          {/* Tabs */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setActiveTab("andamento")}
              className={`rounded-full px-3 py-1.5 text-sm transition ${
                activeTab === "andamento"
                  ? "border border-white/[0.12] bg-[#1a1a1a] text-white"
                  : "text-neutral-500"
              }`}
            >
              Em andamento ({activeItems.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("finalizadas")}
              className={`rounded-full px-3 py-1.5 text-sm transition ${
                activeTab === "finalizadas"
                  ? "border border-white/[0.12] bg-[#1a1a1a] text-white"
                  : "text-neutral-500"
              }`}
            >
              Finalizadas ({finishedItems.length})
            </button>
          </div>

          {/* Ordenação */}
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <span>Ordenar por</span>
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as SortBy)}
              className="rounded-lg border border-white/[0.07] bg-[#131313] px-2 py-1.5 text-sm text-white outline-none"
            >
              <option value="restantes">Parcelas restantes</option>
              <option value="maior_valor">Maior valor da parcela</option>
              <option value="menor_valor">Menor valor da parcela</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="mt-4 space-y-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <LoadingLine key={`inst-list-loading-${index}`} width="w-full" />
            ))}
          </div>
        ) : displayedItems.length === 0 ? (
          <p className="py-8 text-sm text-neutral-500">Nenhum parcelamento para esta aba.</p>
        ) : (
          <div className="mt-3 space-y-2">
            {displayedItems.map((item, i) => (
              <InstallmentCard
                key={`${item.base_name}-${item.original_name}-${item.date}`}
                item={item}
                index={i}
                isExpanded={expandedId === item.base_name}
                onToggle={() => handleToggle(item.base_name)}
              />
            ))}
          </div>
        )}
      </section>
    </PageLayout>
  );
}
