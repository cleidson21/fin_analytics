"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Clock, ChevronRight, Loader2, RefreshCcw } from "lucide-react";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

interface ImportItem {
  id: string;
  source_type: string;
  file_name: string;
  started_at: string;
  status: string;
  rows_read: number;
  rows_inserted: number;
  rows_failed: number;
}

export default function ImportsHubPage() {
  const [items, setItems] = useState<ImportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUnauthorized, setIsUnauthorized] = useState(false);

  async function loadData() {
    setLoading(true);
    setIsUnauthorized(false);
    try {
      const data = await fetchFromAPI<{items: ImportItem[], total: number}>("/governance/imports?limit=50");
      if (data && data.items) {
        setItems(data.items);
      }
    } catch (e: any) {
      if (e.name === "AuthError") setIsUnauthorized(true);
      console.error(e);
    }
    setLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  if (isUnauthorized) {
    return <AuthRequiredCard title="Importações" />;
  }

  function StatusBadge({ status }: { status: string }) {
    if (status === 'CONFIRMED' || status === 'SUCCESS') {
      return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full"><CheckCircle2 className="w-3.5 h-3.5"/> Sucesso</span>;
    }
    if (status === 'RUNNING' || status === 'AWAITING_CONFIRMATION') {
      return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 text-amber-400 text-xs font-medium rounded-full"><Clock className="w-3.5 h-3.5"/> Pendente</span>;
    }
    if (status === 'PARTIAL') {
      return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-sky-500/10 text-sky-400 text-xs font-medium rounded-full"><AlertCircle className="w-3.5 h-3.5"/> Parcial</span>;
    }
    return <span className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-500/10 text-rose-400 text-xs font-medium rounded-full"><AlertCircle className="w-3.5 h-3.5"/> Falha</span>;
  }

  return (
    <PageLayout 
      title="Central de Importações" 
      hideTitle={true}
      breadcrumb={
        <div className="text-sm font-medium text-zinc-500 flex items-center gap-2">
          <Link href="/governance" className="hover:text-white transition-colors">Governança</Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-zinc-300">Importações</span>
        </div>
      }
    >
      <div className="mb-6 flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100 flex items-center gap-3 mb-2">
            <UploadCloud className="w-6 h-6 text-emerald-400" />
            Central de Importações
          </h1>
          <p className="text-zinc-500 text-sm">
            Histórico de sincronizações Pierre Finance e importações de dados MyProfit.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="admin-outline" size="sm" onClick={loadData} disabled={loading}
            className="text-zinc-300 border-white/10 hover:bg-white/5">
            <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Atualizar
          </Button>
          <Link href="/governance/imports/new">
            <Button variant="admin" className="bg-emerald-600 hover:bg-emerald-500">
              <UploadCloud className="h-4 w-4 mr-2" /> Nova Importação
            </Button>
          </Link>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-800 bg-slate-900/50 shadow-xl overflow-hidden flex flex-col h-full mt-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-zinc-400">
            <thead className="bg-black/20 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-6 py-4 font-medium">Data</th>
                <th className="px-6 py-4 font-medium">Origem</th>
                <th className="px-6 py-4 font-medium">Arquivo / Lote</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Lidas</th>
                <th className="px-6 py-4 font-medium text-right">Inseridas</th>
                <th className="px-6 py-4 font-medium text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-transparent">
              {loading && items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-zinc-500">
                    <Loader2 className="inline animate-spin mr-2" size={16} /> Carregando...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-zinc-500">
                    Nenhuma importação encontrada.
                  </td>
                </tr>
              ) : (
                items.map(item => (
                  <tr key={item.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-4 font-mono text-zinc-400">
                      {new Date(item.started_at).toLocaleString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 font-medium text-zinc-200">
                      {item.source_type}
                    </td>
                    <td className="px-6 py-4 text-zinc-400 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-zinc-500" />
                      {item.file_name}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-6 py-4 text-right text-zinc-300 font-mono">
                      {item.rows_read}
                    </td>
                    <td className="px-6 py-4 text-right text-emerald-400 font-mono">
                      {item.rows_inserted}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {item.status === 'RUNNING' || item.status === 'AWAITING_CONFIRMATION' ? (
                        <Link href={`/governance/imports/review?run=${item.id}`}>
                          <Button variant="admin-outline" size="sm" className="text-amber-400 border-amber-500/20 hover:bg-amber-500/10">
                            Revisar
                          </Button>
                        </Link>
                      ) : (
                        <Link href={`/governance/imports/${item.id}`}>
                          <Button variant="admin-outline" size="sm" className="text-zinc-400 border-white/10 hover:text-white hover:bg-white/5">
                            Detalhes
                          </Button>
                        </Link>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </PageLayout>
  );
}
