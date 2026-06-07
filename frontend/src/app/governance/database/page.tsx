"use client";

import { useDatabaseAdmin } from "@/hooks/useDatabaseAdmin";
import { PageLayout } from "@/components/layout/PageLayout";
import { Database, ShieldCheck, AlertTriangle, ShieldAlert, Activity, CheckCircle2, RotateCw, ArrowLeft } from "lucide-react";
import { useState } from "react";
import Link from "next/link";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

export default function DatabaseAdminPage() {
  const { summary, tables, health, integrity, isUnauthorized, vacuumEstimateMutation, vacuumMutation, recountMutation } = useDatabaseAdmin();
  const [showVacuumConfirm, setShowVacuumConfirm] = useState(false);

  if (isUnauthorized) {
    return <AuthRequiredCard title="Banco de Dados" />;
  }

  if (summary.isLoading || tables.isLoading || health.isLoading || integrity.isLoading) {
    return <div className="flex h-screen items-center justify-center text-slate-400">Carregando...</div>;
  }

  const handleVacuumEstimate = async () => {
    await vacuumEstimateMutation.mutateAsync();
    setShowVacuumConfirm(true);
  };

  const handleVacuumConfirm = async () => {
    await vacuumMutation.mutateAsync();
    setShowVacuumConfirm(false);
  };

  return (
    <PageLayout 
      title="Banco de Dados" 
      hideTitle={true}
      breadcrumb={
        <div className="text-sm font-medium text-zinc-500 flex items-center gap-2">
          <Link href="/governance" className="hover:text-white transition-colors">Governança</Link>
          <span>/</span>
          <span className="text-zinc-300">Banco de Dados</span>
        </div>
      }
    >
      {/* Back Button */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link 
          href="/governance"
          className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2 w-4 h-4" />
          Voltar para Dashboard
        </Link>
      </div>

      <div className="space-y-8">
        
        {/* Bloco 2: Health Check */}
        <section>
          <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            Health Check
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Database", status: health.data?.database },
              { label: "Imports", status: health.data?.imports },
              { label: "Wealth", status: health.data?.wealth },
              { label: "Staging", status: health.data?.staging },
            ].map((item, i) => (
              <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                <span className="text-slate-300 font-medium">{item.label}</span>
                {item.status === "OK" ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-amber-500" />
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Bloco 1: KPIs Gerais */}
        <section>
          <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-400" />
            Resumo Geral
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total de Transações" value={summary.data?.total_transactions} />
            <StatCard label="Total de Posições" value={summary.data?.total_positions} />
            <StatCard label="Total de Dividendos" value={summary.data?.total_dividends} />
            <StatCard label="Total de Evoluções" value={summary.data?.total_evolutions} />
            <StatCard label="Total de Importações" value={summary.data?.total_import_runs} />
            <StatCard label="Runs Confirmados" value={summary.data?.runs_confirmed} />
            <StatCard label="Runs Pendentes" value={summary.data?.runs_pending} />
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Bloco 3: Tabelas Monitoradas */}
          <section>
            <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Tabelas Monitoradas
            </h2>
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-800/50 text-slate-400">
                  <tr>
                    <th className="px-4 py-3 font-medium">Nome da Tabela</th>
                    <th className="px-4 py-3 font-medium text-right">Registros</th>
                    <th className="px-4 py-3 font-medium text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {tables.data?.map((table) => (
                    <tr key={table.table_name}>
                      <td className="px-4 py-3 text-slate-200">{table.table_name}</td>
                      <td className="px-4 py-3 text-slate-300 text-right">{table.row_count.toLocaleString('pt-BR')}</td>
                      <td className="px-4 py-3 flex justify-center">
                        <StatusBadge status={table.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="space-y-8">
            {/* Bloco 4: Integridade */}
            <section>
              <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                Integridade
              </h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 space-y-4">
                <div className="flex justify-between items-center pb-4 border-b border-slate-800/50">
                  <span className="text-slate-400">Import Runs Órfãos</span>
                  <span className={`font-mono ${integrity.data?.orphan_runs ? 'text-rose-400 font-bold' : 'text-emerald-400'}`}>
                    {integrity.data?.orphan_runs} detectados
                  </span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-slate-800/50">
                  <span className="text-slate-400">Duplicidades Suspeitas</span>
                  <span className={`font-mono ${integrity.data?.duplicate_transactions_suspects ? 'text-amber-400 font-bold' : 'text-emerald-400'}`}>
                    {integrity.data?.duplicate_transactions_suspects} registros
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Registros Staging Pendentes</span>
                  <span className={`font-mono ${integrity.data?.pending_staging ? 'text-amber-400 font-bold' : 'text-emerald-400'}`}>
                    {integrity.data?.pending_staging} aguardando
                  </span>
                </div>
              </div>
            </section>

            {/* Bloco 5: Operacional */}
            <section>
              <h2 className="text-xl font-semibold text-slate-100 mb-4 flex items-center gap-2">
                <RotateCw className="w-5 h-5 text-indigo-400" />
                Ferramentas Operacionais
              </h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-6">
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-slate-200 font-medium">Recontagem (ANALYZE)</h3>
                    <p className="text-sm text-slate-500">Atualiza as estatísticas do query planner do banco.</p>
                  </div>
                  <button 
                    onClick={() => recountMutation.mutate()}
                    disabled={recountMutation.isPending}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors"
                  >
                    {recountMutation.isPending ? "Processando..." : "Executar"}
                  </button>
                </div>

                <div className="flex items-center justify-between pt-6 border-t border-slate-800/50">
                  <div>
                    <h3 className="text-slate-200 font-medium">Otimizar Espaço (VACUUM)</h3>
                    <p className="text-sm text-slate-500">Compacta o arquivo removendo espaço livre.</p>
                  </div>
                  <button 
                    onClick={handleVacuumEstimate}
                    disabled={vacuumEstimateMutation.isPending}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Estimar VACUUM
                  </button>
                </div>

                {showVacuumConfirm && vacuumEstimateMutation.data && (
                  <div className="bg-slate-800/80 border border-indigo-500/30 p-4 rounded-lg mt-4 animate-in fade-in slide-in-from-top-2">
                    <h4 className="text-indigo-300 font-medium mb-2">Confirmação de VACUUM</h4>
                    <p className="text-sm text-slate-300 mb-4">
                      Tamanho atual: <strong>{vacuumEstimateMutation.data.size_current_kb.toFixed(2)} KB</strong><br/>
                      Estimativa otimizada: <strong>{vacuumEstimateMutation.data.estimated_post_vacuum_kb.toFixed(2)} KB</strong>
                    </p>
                    <div className="flex gap-3">
                      <button 
                        onClick={handleVacuumConfirm}
                        disabled={vacuumMutation.isPending}
                        className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-medium transition-colors flex-1"
                      >
                        {vacuumMutation.isPending ? "Executando..." : "Confirmar VACUUM"}
                      </button>
                      <button 
                        onClick={() => setShowVacuumConfirm(false)}
                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm font-medium transition-colors"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                )}

                {vacuumMutation.isSuccess && vacuumMutation.data && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-sm text-emerald-400">
                    VACUUM concluído com sucesso. Espaço liberado: <strong>{vacuumMutation.data.freed_space_kb.toFixed(2)} KB</strong>
                  </div>
                )}

              </div>
            </section>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}

function StatCard({ label, value }: { label: string; value?: number }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="text-slate-400 text-sm font-medium mb-1">{label}</div>
      <div className="text-2xl font-bold text-slate-100">{value?.toLocaleString('pt-BR') ?? '-'}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'OK') {
    return <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">OK</span>;
  }
  if (status === 'WARNING') {
    return <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-xs font-medium rounded-full">WARNING</span>;
  }
  return <span className="px-2 py-1 bg-rose-500/10 text-rose-400 text-xs font-medium rounded-full">ERROR</span>;
}
