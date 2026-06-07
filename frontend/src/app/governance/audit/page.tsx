"use client";

import { useAuditRuns, useAuditRollbacks } from "@/hooks/useAudit";
import { PageLayout } from "@/components/layout/PageLayout";
import { FileSearch, Clock, History, AlertCircle, CheckCircle2, XCircle, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

type FilterType = "ALL" | "CONFIRMED" | "PENDING" | "ROLLBACK" | "ERROR";

export default function AuditPage() {
  const [filter, setFilter] = useState<FilterType>("ALL");
  const { data: runs, isLoading: loadingRuns, isUnauthorized: runsUnauthorized } = useAuditRuns(filter);
  const { data: rollbacks, isLoading: loadingRollbacks, isUnauthorized: rollbacksUnauthorized } = useAuditRollbacks();
  const router = useRouter();

  if (runsUnauthorized || rollbacksUnauthorized) {
    return <AuthRequiredCard title="Auditoria" />;
  }

  if (loadingRuns || loadingRollbacks) return <div className="flex h-screen items-center justify-center text-slate-400">Carregando...</div>;

  return (
    <PageLayout 
      title="Auditoria" 
      hideTitle={true}
      breadcrumb={
        <div className="text-sm font-medium text-zinc-500 flex items-center gap-2">
          <Link href="/governance" className="hover:text-white transition-colors">Governança</Link>
          <span>/</span>
          <span className="text-zinc-300">Auditoria</span>
        </div>
      }
    >
      {/* Bloco 1: Timeline / Filtros */}
      <section>
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <Link 
            href="/governance"
            className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="mr-2 w-4 h-4" />
            Voltar para Dashboard
          </Link>
          <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1">
              {(["ALL", "CONFIRMED", "PENDING", "ROLLBACK", "ERROR"] as FilterType[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    filter === f 
                      ? 'bg-slate-800 text-slate-100 shadow-sm' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f === "ALL" ? "Todos" : f}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/50 text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Data / Hora</th>
                  <th className="px-4 py-3 font-medium">Arquivo</th>
                  <th className="px-4 py-3 font-medium">Tipo</th>
                  <th className="px-4 py-3 font-medium">Usuário</th>
                  <th className="px-4 py-3 font-medium text-center">Status</th>
                  <th className="px-4 py-3 font-medium text-right">Lidas</th>
                  <th className="px-4 py-3 font-medium text-right">Inseridas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {runs?.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                      Nenhum registro encontrado para este filtro.
                    </td>
                  </tr>
                )}
                {runs?.map((run) => (
                  <tr 
                    key={run.id} 
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                    onClick={() => router.push(`/governance/audit/${run.id}`)}
                  >
                    <td className="px-4 py-3 text-slate-300">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-slate-500" />
                        {new Date(run.started_at).toLocaleString('pt-BR')}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-200">{run.file_name}</td>
                    <td className="px-4 py-3 text-slate-400">{run.source_type}</td>
                    <td className="px-4 py-3 text-slate-400">{run.created_by}</td>
                    <td className="px-4 py-3 flex justify-center">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-300 text-right">{run.rows_read}</td>
                    <td className="px-4 py-3 text-emerald-400 text-right font-medium">{run.rows_inserted}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Bloco 3: Histórico de Rollbacks */}
        <section>
          <h2 className="text-xl font-semibold text-slate-100 mb-6 flex items-center gap-2">
            <History className="w-5 h-5 text-rose-400" />
            Histórico de Rollbacks
          </h2>
          
          <div className="grid gap-4">
            {rollbacks?.length === 0 && (
              <div className="text-slate-500 text-sm p-4 bg-slate-900/30 rounded-lg border border-slate-800/50">
                Nenhum rollback registrado na base.
              </div>
            )}
            {rollbacks?.map((rb) => (
              <div key={rb.id} className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 flex items-start gap-4">
                <div className="p-2 bg-rose-500/10 rounded-full shrink-0">
                  <XCircle className="w-6 h-6 text-rose-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-slate-200 font-medium truncate">
                      Reversão: {rb.file_name}
                    </h3>
                    <span className="text-xs text-slate-500 whitespace-nowrap ml-4">
                      {rb.rollback_timestamp ? new Date(rb.rollback_timestamp).toLocaleString('pt-BR') : 'Desconhecido'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">
                    <span className="text-slate-500">Motivo:</span> {rb.rollback_reason || "Sem justificativa"}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>Run Original: {new Date(rb.started_at).toLocaleString('pt-BR')}</span>
                    <span>Usuário: {rb.rollback_user || 'Sistema'}</span>
                    <span className="font-mono text-slate-600">ID: {rb.id.slice(0, 8)}...</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
    </PageLayout>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'CONFIRMED' || status === 'SUCCESS') {
    return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full"><CheckCircle2 className="w-3.5 h-3.5"/> Confirmado</span>;
  }
  if (status === 'PENDING' || status.includes('AWAITING') || status.includes('PROCESSING')) {
    return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 text-amber-400 text-xs font-medium rounded-full"><Clock className="w-3.5 h-3.5"/> Pendente</span>;
  }
  if (status === 'CANCELLED') {
    return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-500/10 text-slate-400 text-xs font-medium rounded-full"><History className="w-3.5 h-3.5"/> Rollback</span>;
  }
  return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-500/10 text-rose-400 text-xs font-medium rounded-full"><AlertCircle className="w-3.5 h-3.5"/> Erro</span>;
}
