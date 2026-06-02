"use client";

import { useEffect, useMemo, useState } from "react";

import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { getCurrentMonth } from "@/lib/period";
import { formatCurrency } from "@/lib/utils";

interface SubscriptionItem {
  original_name: string;
  date: string;
  amount: number;
}

interface SubscriptionsSummary {
  month: string;
  active_count: number;
  monthly_total: number;
  annual_projection: number;
  average_per_service: number;
  items: SubscriptionItem[];
}

function formatDate(dateValue: string) {
  const date = new Date(`${dateValue}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return dateValue;
  }

  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
}

function LoadingLine({ width = "w-full" }: { width?: string }) {
  return <div className={`h-5 ${width} animate-pulse rounded bg-white/[0.05]`} />;
}

export default function SubscriptionsPage() {
  const [summary, setSummary] = useState<SubscriptionsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const month = useMemo(() => getCurrentMonth(), []);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      const payload = await fetchFromAPI<SubscriptionsSummary>(`/dashboard/subscriptions?month=${month}`);

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
  }, [month]);

  const items = summary?.items ?? [];

  return (
    <PageLayout title="Assinaturas" subtitle={`Serviços recorrentes mapeados em ${month}.`} hideTitle={true}>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {loading || !summary ? (
          Array.from({ length: 4 }).map((_, index) => (
            <article key={`sub-card-loading-${index}`} className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
              <LoadingLine width="w-28" />
              <div className="mt-3">
                <LoadingLine width="w-36" />
              </div>
            </article>
          ))
        ) : (
          [
            { label: "Assinaturas Ativas", value: String(summary.active_count) },
            { label: "Gasto Mensal", value: formatCurrency(summary.monthly_total) },
            { label: "Projeção Anual", value: formatCurrency(summary.annual_projection) },
            { label: "Média por Serviço", value: formatCurrency(summary.average_per_service) },
          ].map((item) => (
            <article key={item.label} className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
              <p className="text-xs uppercase tracking-widest text-neutral-500">{item.label}</p>
              <p className="mt-3 text-2xl font-semibold text-white">{item.value}</p>
            </article>
          ))
        )}
      </section>

      <section className="rounded-xl border border-white/[0.07] bg-[#1a1a1a] p-4">
        <div className="grid grid-cols-[2fr_1fr_1fr] gap-3 border-b border-white/[0.05] pb-3 text-xs uppercase tracking-widest text-neutral-600">
          <span>Serviço</span>
          <span className="text-right">Data</span>
          <span className="text-right">Valor Mensal</span>
        </div>

        {loading ? (
          <div className="mt-3 space-y-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <LoadingLine key={`sub-list-loading-${index}`} width="w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="py-8 text-sm text-neutral-500">Nenhuma assinatura identificada no mês selecionado.</p>
        ) : (
          <div className="mt-2">
            {items.map((item, index) => (
              <article
                key={`${item.original_name}-${item.date}-${index}`}
                className="grid grid-cols-[2fr_1fr_1fr] items-center gap-3 border-b border-white/[0.05] py-3 last:border-b-0"
              >
                <p className="truncate text-sm text-white">{item.original_name}</p>
                <p className="text-right text-sm text-neutral-400">{formatDate(item.date)}</p>
                <p className="text-right text-sm font-medium text-emerald-300">{formatCurrency(item.amount)}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </PageLayout>
  );
}
