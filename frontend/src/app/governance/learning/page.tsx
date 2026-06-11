"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function LearningDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [topRules, setTopRules] = useState<any[]>([]);
  const [probRules, setProbRules] = useState<any[]>([]);
  const [allRules, setAllRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [metRes, topRes, probRes, allRes] = await Promise.all([
          fetch("http://localhost:8000/api/v1/governance/learning/metrics"),
          fetch("http://localhost:8000/api/v1/governance/learning/rules/top?limit=10"),
          fetch("http://localhost:8000/api/v1/governance/learning/rules/problematic?limit=10"),
          fetch("http://localhost:8000/api/v1/governance/learning/rules?limit=50"),
        ]);
        
        const [met, top, prob, all] = await Promise.all([
          metRes.json(), topRes.json(), probRes.json(), allRes.json()
        ]);

        setMetrics(met);
        setTopRules(top);
        setProbRules(prob);
        setAllRules(all);
      } catch (e) {
        console.error("Error loading learning data", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Carregando métricas da Memória Financeira...</div>;
  if (!metrics) return <div className="p-8 text-center text-red-500">Erro ao carregar dados.</div>;

  const getStatusBadge = (status: string) => {
    const colors: any = {
      ACTIVE: "bg-green-500/20 text-green-400 border border-green-500/30",
      OBSERVING: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
      QUARANTINED: "bg-red-500/20 text-red-400 border border-red-500/30",
      RETIRED: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
    };
    const ptBrStatus: any = {
      ACTIVE: "Ativa",
      OBSERVING: "Observando",
      QUARANTINED: "Quarentena",
      RETIRED: "Aposentada"
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || "bg-gray-800 text-gray-300"}`}>
        {ptBrStatus[status] || status}
      </span>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-[#0a0a0a] min-h-screen text-gray-100">
      
      {/* HEADER & HEALTH SCORE */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <Link href="/governance" className="inline-flex items-center text-sm text-gray-400 hover:text-white mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar para Dashboard
          </Link>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Memória Financeira
          </h1>
          <p className="text-gray-400 mt-2">Governança, métricas e observabilidade do aprendizado do sistema.</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col items-center shadow-lg backdrop-blur-sm">
          <span className="text-sm text-gray-400 font-medium tracking-wide uppercase">Saúde da Memória</span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className={`text-4xl font-bold ${metrics.memory_health_score >= 90 ? 'text-emerald-400' : metrics.memory_health_score >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
              {metrics.memory_health_score}%
            </span>
          </div>
          <span className="text-xs text-gray-500 mt-1">Acertos Globais</span>
        </div>
      </div>

      {/* KPI GRID */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total de Regras", value: metrics.total_rules, color: "text-blue-400" },
          { label: "Ativas", value: metrics.active_rules || 0, color: "text-green-400" },
          { label: "Observando", value: metrics.observing_rules || 0, color: "text-indigo-400" },
          { label: "Quarentena", value: metrics.quarantined_rules || 0, color: "text-red-400" },
        ].map((kpi, idx) => (
          <div key={idx} className="bg-slate-900/40 border border-slate-800 p-5 rounded-xl hover:border-slate-700 transition-colors">
            <div className="text-sm text-gray-500 font-medium">{kpi.label}</div>
            <div className={`text-3xl font-semibold mt-2 ${kpi.color}`}>{kpi.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* TOP RULES */}
        <div className="bg-slate-900/30 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-96">
          <div className="p-4 border-b border-slate-800 bg-slate-900/50">
            <h2 className="text-lg font-medium text-emerald-400 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              Top 10 Regras
            </h2>
          </div>
          <div className="p-4 overflow-y-auto flex-1 space-y-3">
            {topRules.length === 0 ? <p className="text-gray-500 text-sm">Nenhuma regra ativa.</p> : null}
            {topRules.map(r => (
              <div key={r.id} className="bg-slate-800/30 p-3 rounded-lg flex justify-between items-center border border-slate-800/50 hover:border-emerald-500/30 transition-colors">
                <div className="overflow-hidden">
                  <div className="text-sm font-medium text-gray-200 truncate">{r.pattern}</div>
                  <div className="text-xs text-gray-500 mt-1">{r.rule_type} • {r.hit_count} hits</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-emerald-400 text-sm font-bold">{(r.confidence_score * 100).toFixed(1)}%</div>
                  </div>
                  {getStatusBadge(r.status)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PROBLEMATIC RULES */}
        <div className="bg-slate-900/30 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-96">
          <div className="p-4 border-b border-slate-800 bg-slate-900/50">
            <h2 className="text-lg font-medium text-red-400 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              Regras Degradadas
            </h2>
          </div>
          <div className="p-4 overflow-y-auto flex-1 space-y-3">
            {probRules.length === 0 ? <p className="text-gray-500 text-sm">Nenhuma regra degradada.</p> : null}
            {probRules.map(r => (
              <div key={r.id} className="bg-slate-800/30 p-3 rounded-lg flex justify-between items-center border border-slate-800/50 hover:border-slate-500/30 transition-colors">
                <div className="overflow-hidden">
                  <div className="text-sm font-medium text-gray-200 truncate">{r.pattern}</div>
                  <div className="text-xs text-gray-500 mt-1">{r.miss_count} misses • {r.evidence_count} evidências</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-red-400 text-sm font-bold">{(r.confidence_score * 100).toFixed(1)}%</div>
                  </div>
                  {getStatusBadge(r.status)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FULL AUDIT TABLE */}
      <div className="bg-slate-900/30 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-200">Auditoria Completa de Regras</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="text-xs text-gray-500 uppercase bg-slate-900/80 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Tipo</th>
                <th className="px-6 py-4">Padrão Identificado</th>
                <th className="px-6 py-4">Score</th>
                <th className="px-6 py-4">Hits/Misses</th>
                <th className="px-6 py-4 text-right">Atualização</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {allRules.map((rule) => (
                <tr key={rule.id} className="hover:bg-slate-800/20 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(rule.status)}</td>
                  <td className="px-6 py-4 font-medium text-gray-300">{rule.rule_type}</td>
                  <td className="px-6 py-4 font-mono text-xs text-gray-400 max-w-[250px] truncate" title={rule.pattern}>{rule.pattern}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${rule.confidence_score >= 0.8 ? 'bg-emerald-500' : rule.confidence_score >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{ width: `${rule.confidence_score * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-medium text-gray-300">{(rule.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-emerald-400">{rule.hit_count}</span>
                    <span className="text-gray-600 mx-1">/</span>
                    <span className="text-red-400">{rule.miss_count}</span>
                  </td>
                  <td className="px-6 py-4 text-right whitespace-nowrap text-xs">
                    {format(new Date(rule.status_changed_at || rule.created_at), "dd MMM yyyy HH:mm")}
                  </td>
                </tr>
              ))}
              {allRules.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    A memória financeira está vazia. O sistema começará a aprender conforme o uso.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
