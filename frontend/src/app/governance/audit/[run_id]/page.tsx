"use client";

import { use } from "react";
import { useAuditRunDetail } from "@/hooks/useAudit";
import { TopNav } from "@/components/layout/TopNav";
import { FileSearch, Clock, ArrowLeft, CheckCircle2, AlertCircle, History, RotateCw, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchFromAPI } from "@/lib/api";

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

import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

export default function AuditRunPage({ params }: { params: Promise<{ run_id: string }> }) {
  const resolvedParams = use(params);
  const { data: run, isLoading, isUnauthorized } = useAuditRunDetail(resolvedParams.run_id);
  const router = useRouter();

  const [isReprocessing, setIsReprocessing] = useState(false);
  const [reprocessError, setReprocessError] = useState<string | null>(null);

  if (isUnauthorized) {
    return <AuthRequiredCard title="Auditoria" />;
  }

  const handleReprocess = async () => {
    setIsReprocessing(true);
    setReprocessError(null);
    try {
      const data = await fetchFromAPI<{run_id: string}>(`/governance/imports/${resolvedParams.run_id}/reprocess`, {
        method: "POST"
      });
      if (!data || !data.run_id) {
        throw new Error("Falha ao reprocessar");
      }
      router.push(`/governance/review?run=${data.run_id}`);
    } catch (err: any) {
      setReprocessError(err.message || "Erro desconhecido ao reprocessar");
      setIsReprocessing(false);
    }
  };

  if (isLoading) return <div className="flex h-screen items-center justify-center text-slate-400">Carregando...</div>;
  if (!run) return <div className="flex h-screen items-center justify-center text-rose-400">Run não encontrado</div>;

  return (
    <div className="min-h-screen bg-slate-950 pb-20">

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        
        <Link href="/governance/audit" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Voltar para Auditoria
        </Link>

        <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <div className="flex items-start justify-between mb-8 pb-6 border-b border-slate-800/50">
            <div>
              <h1 className="text-2xl font-semibold text-slate-100 flex items-center gap-3 mb-2">
                <FileSearch className="w-6 h-6 text-indigo-400" />
                Detalhamento da Importação
              </h1>
              <div className="text-sm text-slate-500 font-mono">ID: {run.id}</div>
            </div>
            <div className="flex flex-col items-end gap-3">
              <StatusBadge status={run.status} />
              {(run.status === "SUCCESS" || run.status === "CONFIRMED" || run.status === "FAILED" || run.status === "CANCELLED" || run.status === "PARTIAL") && (
                <Button 
                  variant="admin"
                  onClick={handleReprocess} 
                  disabled={isReprocessing}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white shadow-md text-sm h-8"
                >
                  {isReprocessing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RotateCw className="w-4 h-4 mr-2" />}
                  Reprocessar
                </Button>
              )}
              {reprocessError && <span className="text-xs text-rose-400">{reprocessError}</span>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">Arquivo</div>
                <div className="font-medium text-slate-200">{run.file_name || "Sem nome"}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">Data / Hora</div>
                <div className="font-medium text-slate-200">{new Date(run.started_at).toLocaleString('pt-BR')}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">Usuário</div>
                <div className="font-medium text-slate-200">{run.created_by || "Sistema"}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">Tipo de Fonte</div>
                <div className="font-medium text-slate-200">{run.source_type}</div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">Linhas Lidas</div>
                <div className="font-medium text-slate-200">{run.rows_read}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">Linhas Inseridas</div>
                <div className="font-medium text-emerald-400">{run.rows_inserted}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">Linhas Atualizadas</div>
                <div className="font-medium text-blue-400">{run.rows_updated}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">Linhas Falhas</div>
                <div className="font-medium text-rose-400">{run.rows_failed}</div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
