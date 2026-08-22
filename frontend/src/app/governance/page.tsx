"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  UploadCloud, RefreshCcw, AlertTriangle, Loader2,
  ShieldCheck, Database, History, ArrowRight,
} from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";

// ==========================================================================
// TYPES
// ==========================================================================

interface GovernanceSummary {
  total_entrada: number;
  total_saida: number;
  resultado: number;
  pending_count: number;
  classified_count: number;
  ignored_count: number;
}

// ==========================================================================
// HELPERS
// ==========================================================================

function fmt(v: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

// ==========================================================================
// PAGE — Visao Geral da Governanca
// ==========================================================================

export default function GovernanceDashboardPage() {
  const [summary, setSummary] = useState<GovernanceSummary | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadSummary() {
    setLoading(true);
    const data = await fetchFromAPI<GovernanceSummary>("/governance/summary");
    if (data) setSummary(data);
    setLoading(false);
  }

  useEffect(() => { loadSummary(); }, []);

  return (
    <PageLayout title="Governança" hideTitle={true}>

      {/* Header actions */}
      <div className="mb-6 flex items-center justify-end gap-3 flex-wrap">
        <div className="flex gap-3">
          <Button variant="admin-outline" size="sm" onClick={loadSummary} disabled={loading}
            className="text-zinc-300 border-white/10 hover:bg-white/5">
            <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Atualizar
          </Button>
          <Link href="/governance/imports">
            <Button variant="admin"><UploadCloud className="h-4 w-4 mr-2" /> Nova Importação MyProfit</Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      {loading ? (
        <div className="text-center py-12 text-zinc-500">
          <Loader2 className="inline animate-spin mr-2" size={16} /> Carregando...
        </div>
      ) : summary ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {[
              { label: "Entradas Classificadas", value: fmt(summary.total_entrada), color: "text-emerald-400", bg: "border-emerald-500/20" },
              { label: "Saidas Classificadas",   value: fmt(summary.total_saida),   color: "text-red-400",     bg: "border-red-500/20"     },
              { label: "Resultado",              value: fmt(summary.resultado),      color: summary.resultado >= 0 ? "text-emerald-400" : "text-red-400", bg: "border-white/10" },
              { label: "Classificadas",          value: String(summary.classified_count), color: "text-indigo-400", bg: "border-indigo-500/20" },
              { label: "Ignoradas",              value: String(summary.ignored_count),    color: "text-amber-400",  bg: "border-amber-500/20"  },
              { label: "Pendentes",              value: String(summary.pending_count),    color: "text-zinc-400",   bg: "border-zinc-500/20"   },
            ].map(({ label, value, color, bg }) => (
              <div key={label} className={`rounded-2xl border ${bg} bg-slate-900/50 p-5`}>
                <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-3">{label}</p>
                <p className={`text-2xl font-semibold ${color}`}>{value}</p>
              </div>
            ))}
          </div>

          {summary.pending_count > 0 && (
            <div style={{
              background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)",
              borderRadius: "12px", padding: "14px 18px", marginBottom: "24px",
              display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <AlertTriangle size={16} color="#f59e0b" />
                <span style={{ color: "#fbbf24", fontSize: "13px" }}>
                  <strong>{summary.pending_count}</strong> transações aguardam classificação manual.
                </span>
              </div>
              <Link href="/governance/classify" style={{
                display: "flex", alignItems: "center", gap: "6px",
                padding: "8px 14px", borderRadius: "8px",
                background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)",
                color: "#f59e0b", fontSize: "12px", fontWeight: 600, textDecoration: "none",
                whiteSpace: "nowrap",
              }}>
                Classificar agora <ArrowRight size={13} />
              </Link>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-zinc-500">
          Não foi possível carregar o resumo. Verifique a conexão com a API.
        </div>
      )}

      {/* Quick links */}
      <div className="grid sm:grid-cols-3 gap-4 mt-2">
        {[
          {
            href: "/governance/classify",
            icon: <ShieldCheck className="h-5 w-5 text-indigo-400" />,
            title: "Classificações",
            desc: "Classifique transações Pierre Finance como ENTRADA, SAÍDA ou IGNORAR",
          },
          {
            href: "/governance/imports",
            icon: <UploadCloud className="h-5 w-5 text-emerald-400" />,
            title: "Importações MyProfit",
            desc: "Importe dados da plataforma MyProfit",
          },
          {
            href: "/governance/audit",
            icon: <History className="h-5 w-5 text-rose-400" />,
            title: "Auditoria",
            desc: "Histórico de alterações e rollbacks de governança",
          },
          {
            href: "/governance/data",
            icon: <Database className="h-5 w-5 text-blue-400" />,
            title: "MyProfit",
            desc: "Consulte os dados brutos da plataforma MyProfit (somente leitura)",
          },
        ].map(({ href, icon, title, desc }) => (
          <Link key={href} href={href} className="group rounded-2xl border border-slate-800 bg-slate-900/50 p-5 hover:border-slate-700 hover:bg-slate-800/50 transition-colors">
            <div className="flex items-center gap-3 mb-3">
              {icon}
              <span className="text-white font-medium text-sm">{title}</span>
            </div>
            <p className="text-zinc-500 text-xs leading-relaxed">{desc}</p>
          </Link>
        ))}
      </div>

    </PageLayout>
  );
}
