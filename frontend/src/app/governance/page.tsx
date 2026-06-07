"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  ArrowRight, 
  Activity, 
  CheckCircle2, 
  Clock, 
  UploadCloud, 
  List, 
  Eye, 
  DatabaseBackup,
  RefreshCcw
} from "lucide-react";

import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

interface DashboardMetrics {
  total_runs: number;
  confirmed_runs: number;
  pending_runs: number;
  lines_inserted: number;
  lines_updated: number;
  lines_failed: number;
  last_import: string | null;
}

interface ImportRunItem {
  id: string;
  source_type: string;
  file_name: string;
  started_at: string;
  status: string;
  rows_read: number;
  rows_inserted: number;
  rows_failed: number;
}

interface ImportRunListResponse {
  items: ImportRunItem[];
  total: number;
}

export default function GovernanceDashboardPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentRuns, setRecentRuns] = useState<ImportRunItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUnauthorized, setIsUnauthorized] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    setIsUnauthorized(false);
    try {
      const [metricsData, runsData] = await Promise.all([
        fetchFromAPI<DashboardMetrics>("/governance/dashboard"),
        fetchFromAPI<ImportRunListResponse>("/governance/imports?limit=10")
      ]);
      
      if (metricsData) setMetrics(metricsData);
      if (runsData && runsData.items) {
        setRecentRuns(runsData.items.filter((r) => r.source_type !== "LEGACY"));
      }
    } catch (err: any) {
      if (err.name === "AuthError") {
        setIsUnauthorized(true);
      } else {
        console.error("Failed to load dashboard data", err);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (isUnauthorized) {
    return <AuthRequiredCard title="Governança" />;
  }

  function renderStatusBadge(status: string) {
    if (status === "SUCCESS") return <span className="rounded bg-emerald-500/20 px-2 py-1 text-xs text-emerald-300">Sucesso</span>;
    if (status === "CONFIRMED") return <span className="rounded bg-blue-500/20 px-2 py-1 text-xs text-blue-300">Confirmado</span>;
    if (status === "AWAITING_CONFIRMATION") return <span className="rounded bg-yellow-500/20 px-2 py-1 text-xs text-yellow-300">Aguardando</span>;
    if (status === "FAILED") return <span className="rounded bg-red-500/20 px-2 py-1 text-xs text-red-300">Falha</span>;
    if (status === "PARTIAL") return <span className="rounded bg-amber-500/20 px-2 py-1 text-xs text-amber-300">Parcial</span>;
    if (status === "PROCESSING" || status === "PROCESSING_CONFIRMATION") return <span className="rounded bg-purple-500/20 px-2 py-1 text-xs text-purple-300">Processando</span>;
    return <span className="rounded bg-zinc-500/20 px-2 py-1 text-xs text-zinc-400">{status}</span>;
  }

  return (
    <PageLayout title="Governança de Dados" subtitle="Visão geral e controle do fluxo de importação" hideTitle={true}>
      {/* Header Actions */}
      <div className="mb-4 flex items-center justify-end">
        <div className="flex gap-3">
          <Button variant="admin-outline" size="sm" onClick={loadDashboard} disabled={loading} className="text-zinc-300 border-white/10 hover:bg-white/5">
            <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Link
            href="/governance/imports"
          >
            <Button variant="admin">
              <UploadCloud className="h-4 w-4 mr-2" />
              Nova Importação
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3 text-zinc-400">
            <Activity className="h-5 w-5 text-emerald-400" />
            <span className="text-sm font-medium uppercase tracking-wider">Total Runs</span>
          </div>
          <p className="mt-4 text-3xl font-semibold text-white">{metrics?.total_runs ?? "-"}</p>
          <p className="mt-1 text-xs text-zinc-500">
            Último: {metrics?.last_import ? new Date(metrics.last_import).toLocaleDateString('pt-BR') : 'N/A'}
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3 text-zinc-400">
            <CheckCircle2 className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-medium uppercase tracking-wider">Confirmados</span>
          </div>
          <p className="mt-4 text-3xl font-semibold text-white">{metrics?.confirmed_runs ?? "-"}</p>
          <p className="mt-1 text-xs text-zinc-500">Importações efetivadas</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3 text-zinc-400">
            <Clock className="h-5 w-5 text-yellow-400" />
            <span className="text-sm font-medium uppercase tracking-wider">Pendentes</span>
          </div>
          <p className="mt-4 text-3xl font-semibold text-white">{metrics?.pending_runs ?? "-"}</p>
          <p className="mt-1 text-xs text-zinc-500">Aguardando revisão</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3 text-zinc-400">
            <DatabaseBackup className="h-5 w-5 text-purple-400" />
            <span className="text-sm font-medium uppercase tracking-wider">Linhas Salvas</span>
          </div>
          <p className="mt-4 text-3xl font-semibold text-white">{metrics?.lines_inserted ?? "-"}</p>
          <div className="mt-1 flex gap-2 text-xs">
            <span className="text-emerald-400">+{metrics?.lines_updated ?? 0} upd</span>
            <span className="text-red-400">{metrics?.lines_failed ?? 0} err</span>
          </div>
        </div>
      </div>

      {/* Recent Runs Table */}
      <section className="rounded-2xl border border-white/10 bg-white/5 shadow-xl">
        <div className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <List className="h-5 w-5 text-zinc-300" />
            <h3 className="font-medium text-white">Últimas Importações</h3>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-black/20 text-zinc-400">
              <tr>
                <th className="px-6 py-3 font-medium">Data</th>
                <th className="px-6 py-3 font-medium">Arquivo</th>
                <th className="px-6 py-3 font-medium">Tipo</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-zinc-300">
              {loading && recentRuns.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-zinc-500">Carregando histórico...</td>
                </tr>
              ) : recentRuns.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-zinc-500">Nenhuma importação encontrada.</td>
                </tr>
              ) : (
                recentRuns.map((run) => (
                  <tr key={run.id} className="transition-colors hover:bg-white/5">
                    <td className="px-6 py-4">{new Date(run.started_at).toLocaleDateString('pt-BR')}</td>
                    <td className="px-6 py-4">
                      <span className="block font-medium text-zinc-200">{run.file_name || 'Upload Direto'}</span>
                      <span className="text-xs font-mono text-zinc-500">ID: {run.id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-6 py-4 text-zinc-400">{run.source_type}</td>
                    <td className="px-6 py-4">{renderStatusBadge(run.status)}</td>
                    <td className="px-6 py-4 text-right">
                      {(run.status === 'AWAITING_CONFIRMATION' || run.status === 'CONFIRMED' || run.status === 'FAILED') && (
                        <Button
                          variant="admin-ghost"
                          size="sm"
                          onClick={() => router.push(`/governance/review?run=${run.id}`)}
                          className={`h-8 ${run.status === 'AWAITING_CONFIRMATION' ? 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-400/10' : 'text-zinc-400 hover:text-white'}`}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          {run.status === 'AWAITING_CONFIRMATION' ? 'Revisar' : 'Detalhes'}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </PageLayout>
  );
}