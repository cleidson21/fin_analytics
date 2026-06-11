"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  ChevronRight,
  DatabaseBackup,
  Trash2,
  Loader2,
  FileText
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

interface ImportRunDetail {
  id: string;
  source_type: string;
  file_name: string;
  checksum: string;
  started_at: string;
  finished_at: string | null;
  status: string;
  rows_read: number;
  rows_inserted: number;
  rows_updated: number;
  rows_failed: number;
  created_by: string;
  error_log: string | null;
  preview_summary?: string | null;
}

interface StagingItem {
  source_line_no: number;
  ticker: string | null;
  validation_status: string;
  validation_message: string | null;
}

interface StagingData {
  run_id: string;
  file_type: string;
  items: StagingItem[];
}

function ReviewContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const runId = searchParams?.get("run");

  const [runData, setRunData] = useState<ImportRunDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState<string | null>(null);
  const [stagingData, setStagingData] = useState<StagingData | null>(null);
  const [parsedLog, setParsedLog] = useState<{ warnings: string[], errors: string[] } | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [isUnauthorized, setIsUnauthorized] = useState(false);

  useEffect(() => {
    if (runId) {
      loadRunDetails(runId);
    }
  }, [runId]);

  async function loadRunDetails(id: string) {
    setLoading(true);
    setIsUnauthorized(false);
    try {
      const data = await fetchFromAPI<ImportRunDetail>(`/governance/imports/${id}`);
      setRunData(data);
      if (!data) return;

      if (data.error_log) {
        try {
          const parsed = JSON.parse(data.error_log);
          setParsedLog(parsed);
        } catch {
          setParsedLog({ warnings: [], errors: [data.error_log] });
        }
      }

      try {
        const sData = await fetchFromAPI<StagingData>(`/governance/imports/${id}/staging-items`);
        setStagingData(sData);
      } catch {
        console.error("Erro ao buscar itens do staging");
      }
    } catch (e: any) {
      if (e.name === "AuthError") {
        setIsUnauthorized(true);
      } else {
        console.error("Failed to load run details", e);
      }
    }
    setLoading(false);
  }

  async function handleConfirm() {
    if (!runData) return;
    setConfirming(true);
    setConfirmMessage(null);
    try {
      await fetchFromAPI(`/governance/imports/${runData.id}/confirm`, { method: "POST" });
      setConfirmMessage("Importação confirmada com sucesso!");
      loadRunDetails(runData.id);
    } catch (e: any) {
      setConfirmMessage("Erro ao confirmar: " + e.message);
    } finally {
      setConfirming(false);
    }
  }

  async function handleCancel() {
    if (!runData) return;
    if (!confirm("Tem certeza que deseja cancelar e descartar esta importação?")) return;
    
    setConfirming(true);
    setConfirmMessage(null);
    try {
      await fetchFromAPI(`/governance/imports/${runData.id}/rollback`, { method: "POST" });
      router.push('/governance');
    } catch (e: any) {
      setConfirmMessage("Erro ao cancelar: " + e.message);
      setConfirming(false);
    }
  }

  function renderStatusBadge(status: string) {
    if (status === "SUCCESS") return <span className="rounded bg-emerald-500/20 px-2 py-1 text-sm text-emerald-300">Sucesso</span>;
    if (status === "PARTIAL") return <span className="rounded bg-amber-500/20 px-2 py-1 text-sm text-amber-300">Parcial</span>;
    if (status === "FAILED") return <span className="rounded bg-red-500/20 px-2 py-1 text-sm text-red-300">Falha</span>;
    if (status === "CONFIRMED") return <span className="rounded bg-blue-500/20 px-2 py-1 text-sm text-blue-300">Efetivado</span>;
    if (status === "AWAITING_CONFIRMATION") return <span className="rounded bg-yellow-500/20 px-2 py-1 text-sm text-yellow-300">Aguardando</span>;
    return <span className="rounded bg-zinc-500/20 px-2 py-1 text-sm text-zinc-300">{status}</span>;
  }

  const getCounters = () => {
    if (!stagingData) return { valid: 0, update: 0, unchanged: 0, error: 0 };
    return {
      valid: stagingData.items.filter(i => i.validation_status === 'VALID' || i.validation_status === 'WARNING').length,
      update: stagingData.items.filter(i => i.validation_status === 'UPDATE').length,
      unchanged: stagingData.items.filter(i => i.validation_status === 'UNCHANGED' || i.validation_status === 'DUPLICATE').length,
      error: stagingData.items.filter(i => i.validation_status === 'ERROR' || i.validation_status === 'CONFLICT').length,
    };
  };
  const counters = getCounters();

  if (isUnauthorized) {
    return <AuthRequiredCard title="Revisão de Importação" />;
  }

  return (
    <PageLayout title="Revisão de Importação" subtitle="" hideTitle={true}>
      {/* Breadcrumb TopBar */}
      <div className="mb-6 flex items-center justify-between border-b border-white/10 pb-4">
        <nav className="flex items-center text-sm text-zinc-400">
          <Link href="/governance" className="hover:text-emerald-400 transition-colors flex items-center">
            <DatabaseBackup className="mr-2 h-4 w-4" />
            Dashboard
          </Link>
          <ChevronRight className="mx-2 h-4 w-4" />
          <Link href="/governance/imports" className="hover:text-emerald-400 transition-colors">
            Importações
          </Link>
          <ChevronRight className="mx-2 h-4 w-4" />
          <span className="text-zinc-200 font-medium">Revisar Run</span>
        </nav>
      </div>

      {!runId && (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-white/10 bg-black/20 text-center">
          <p className="text-sm font-medium text-zinc-400">Nenhum Run ID fornecido.</p>
        </div>
      )}

      {loading && runId && (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-white/10 bg-black/20 text-center">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
          <p className="mt-4 text-sm font-medium text-zinc-400">Carregando detalhes da execução...</p>
        </div>
      )}

      {!loading && runData && (
        <div className="space-y-6">
          {/* Main Info Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-3xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">Revisão: {runData.file_name}</h1>
              <p className="text-sm text-zinc-400 font-mono">ID: {runData.id} • Data: {new Date(runData.started_at).toLocaleString()}</p>
            </div>
            <div className="flex items-center gap-4">
              {renderStatusBadge(runData.status)}
              {runData.status === 'AWAITING_CONFIRMATION' && (
                <div className="flex items-center gap-3 ml-4 border-l border-white/10 pl-4">
                  <Button variant="admin-outline" onClick={handleCancel} disabled={confirming} className="border-red-500/20 text-red-400 hover:bg-red-500/10">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Cancelar
                  </Button>
                  <Button variant="admin" onClick={handleConfirm} disabled={confirming} className="bg-emerald-600 hover:bg-emerald-500">
                    {confirming ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                    Confirmar Importação
                  </Button>
                </div>
              )}
            </div>
          </div>
          
          {confirmMessage && (
            <div className={`p-4 rounded-xl border ${confirmMessage.includes('Erro') ? 'border-red-500/30 bg-red-500/10 text-red-400' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'}`}>
              {confirmMessage}
            </div>
          )}

          {/* Resumo Counters */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 flex flex-col items-center justify-center">
              <span className="text-sm font-medium text-emerald-400/70 uppercase tracking-wider mb-2">Válidos (Novos)</span>
              <span className="text-4xl font-bold text-emerald-400">{counters.valid}</span>
            </div>
            <div className="rounded-2xl border border-sky-500/20 bg-sky-500/5 p-5 flex flex-col items-center justify-center">
              <span className="text-sm font-medium text-sky-400/70 uppercase tracking-wider mb-2">Atualizados</span>
              <span className="text-4xl font-bold text-sky-400">{counters.update}</span>
            </div>
            <div className="rounded-2xl border border-zinc-500/20 bg-zinc-500/5 p-5 flex flex-col items-center justify-center">
              <span className="text-sm font-medium text-zinc-400/70 uppercase tracking-wider mb-2">Ignorados</span>
              <span className="text-4xl font-bold text-zinc-400">{counters.unchanged}</span>
            </div>
            <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 flex flex-col items-center justify-center">
              <span className="text-sm font-medium text-red-400/70 uppercase tracking-wider mb-2">Erros</span>
              <span className="text-4xl font-bold text-red-400">{counters.error}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Table of items */}
            <div className="lg:col-span-2">
              <section className="rounded-3xl border border-slate-800 bg-slate-900/50 shadow-xl overflow-hidden flex flex-col h-full">
                <div className="p-5 border-b border-white/10 flex flex-wrap justify-between items-center gap-4">
                  <h2 className="text-lg font-semibold text-white">Linhas do Arquivo</h2>
                  <div className="flex gap-2">
                    {[
                      { val: "ALL", label: "TUDO" },
                      { val: "VALID", label: "VÁLIDOS" },
                      { val: "UPDATE", label: "ATUALIZADOS" },
                      { val: "UNCHANGED", label: "IGNORADOS" },
                      { val: "ERROR", label: "ERROS" }
                    ].map(f => (
                      <button 
                        key={f.val} 
                        onClick={() => setFilter(f.val)} 
                        className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${filter === f.val ? 'bg-white text-black' : 'bg-black/30 border border-white/10 text-zinc-400 hover:bg-white/10'}`}>
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-zinc-400">
                    <thead className="bg-black/20 text-xs uppercase text-zinc-500">
                      <tr>
                        <th className="px-6 py-4 font-medium">Linha</th>
                        <th className="px-6 py-4 font-medium">Ativo/Referência</th>
                        <th className="px-6 py-4 font-medium">Status</th>
                        <th className="px-6 py-4 font-medium">Observação</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-transparent">
                      {stagingData?.items
                        .filter(i => {
                          if (filter === "ALL") return true;
                          if (filter === "VALID") return i.validation_status === "VALID" || i.validation_status === "WARNING";
                          if (filter === "ERROR") return i.validation_status === "ERROR" || i.validation_status === "CONFLICT";
                          if (filter === "UNCHANGED") return i.validation_status === "UNCHANGED" || i.validation_status === "DUPLICATE";
                          return i.validation_status === filter;
                        })
                        .map(item => {
                        return (
                          <tr key={item.source_line_no} className="hover:bg-white/5 transition-colors">
                            <td className="px-6 py-4 font-mono text-zinc-500">{item.source_line_no}</td>
                            <td className="px-6 py-4 font-medium text-zinc-200">{item.ticker || '-'}</td>
                            <td className="px-6 py-4">
                              {(() => {
                                const map: Record<string, string> = {
                                  "VALID": "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
                                  "WARNING": "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
                                  "CONFLICT": "bg-red-500/20 text-red-400 border border-red-500/30",
                                  "ERROR": "bg-red-500/20 text-red-400 border border-red-500/30",
                                  "IMPORTED": "bg-blue-500/20 text-blue-400 border border-blue-500/30",
                                  "UNCHANGED": "bg-zinc-500/20 text-zinc-400 border border-zinc-500/30",
                                  "UPDATE": "bg-sky-500/20 text-sky-400 border border-sky-500/30",
                                  "PENDING": "bg-zinc-500/20 text-zinc-400 border border-zinc-500/30"
                                };
                                const ptLabels: Record<string, string> = {
                                  "VALID": "VÁLIDO",
                                  "WARNING": "VÁLIDO (AVISO)",
                                  "CONFLICT": "ERRO (CONFLITO)",
                                  "ERROR": "ERRO",
                                  "IMPORTED": "IMPORTADO",
                                  "UNCHANGED": "IGNORADO",
                                  "UPDATE": "ATUALIZADO",
                                  "PENDING": "PENDENTE"
                                };
                                const badgeClass = map[item.validation_status] || map["PENDING"];
                                const label = ptLabels[item.validation_status] || item.validation_status;
                                return <span className={`px-2.5 py-1 rounded-md text-xs font-semibold ${badgeClass}`}>{label}</span>;
                              })()}
                            </td>
                            <td className="px-6 py-4 max-w-xs truncate text-zinc-400" title={item.validation_message || ''}>{item.validation_message || '-'}</td>
                          </tr>
                        )
                      })}
                      {stagingData?.items.filter(i => {
                        if (filter === "ALL") return true;
                        if (filter === "VALID") return i.validation_status === "VALID" || i.validation_status === "WARNING";
                        if (filter === "ERROR") return i.validation_status === "ERROR" || i.validation_status === "CONFLICT";
                        if (filter === "UNCHANGED") return i.validation_status === "UNCHANGED" || i.validation_status === "DUPLICATE";
                        return i.validation_status === filter;
                      }).length === 0 && (
                        <tr>
                          <td colSpan={4} className="py-12 text-center text-zinc-500">Nenhum registro para exibir.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            {/* Logs Column */}
            <div className="space-y-6">
              <section className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl h-full">
                <div className="mb-4 flex items-center gap-2 border-b border-white/10 pb-4">
                  <FileText className="h-5 w-5 text-zinc-400" />
                  <h2 className="text-lg font-semibold text-white">Log de Detalhes</h2>
                </div>

                {!parsedLog && !runData.error_log && counters.error === 0 && (
                  <p className="text-sm text-zinc-500 text-center py-8">Nenhum erro ou aviso registrado.</p>
                )}

                {parsedLog?.errors && parsedLog.errors.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-3">
                      <XCircle className="h-5 w-5 text-red-400" />
                      <span className="text-sm font-medium text-red-300">Erros Bloqueantes ({parsedLog.errors.length})</span>
                    </div>
                    <ul className="space-y-2">
                      {parsedLog.errors.map((err, i) => (
                        <li key={i} className="text-sm text-red-200/80 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                          {err}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {parsedLog?.warnings && parsedLog.warnings.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="h-5 w-5 text-amber-400" />
                      <span className="text-sm font-medium text-amber-300">Avisos ({parsedLog.warnings.length})</span>
                    </div>
                    <ul className="space-y-2">
                      {parsedLog.warnings.map((warn, i) => (
                        <li key={i} className="text-sm text-amber-200/80 bg-amber-500/10 p-3 rounded-lg border border-amber-500/20">
                          {warn}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {runData.error_log && !parsedLog && (
                  <div className="mt-4 rounded-xl bg-black/40 p-4 text-xs font-mono text-red-300 whitespace-pre-wrap overflow-x-auto border border-red-500/10">
                    {runData.error_log}
                  </div>
                )}
              </section>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
}

export default function GovernanceReviewPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center text-slate-400"><Loader2 className="h-6 w-6 animate-spin mr-2" />Carregando...</div>}>
      <ReviewContent />
    </Suspense>
  );
}
