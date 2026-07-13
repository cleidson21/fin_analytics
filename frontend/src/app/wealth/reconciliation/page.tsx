"use client";

import { useState, useMemo, useEffect } from "react";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { formatCurrency, colorForValue } from "@/lib/utils";
import { fetchFromAPI } from "@/lib/api";
import { CheckCircle, AlertTriangle, XCircle, Search, Filter, ShieldCheck, Activity } from "lucide-react";

export interface ReconciliationResult {
  ticker: string;
  broker: string;
  ledger_quantity: number;
  snapshot_quantity: number;
  difference: number;
  difference_percent: number;
  status: "OK" | "WARNING" | "ERROR";
  recommendation: string;
}

export default function ReconciliationPage() {
  const [data, setData] = useState<ReconciliationResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "OK" | "WARNING" | "ERROR">("ALL");
  const [sortBy, setSortBy] = useState<"ticker" | "difference" | "percent">("difference");

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      try {
        const res = await fetchFromAPI<ReconciliationResult[]>("/investments/reconciliation");
        if (mounted && res) {
          setData(res);
        } else if (mounted) {
          setIsError(true);
        }
      } catch {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  const { filteredData, kpis } = useMemo(() => {
    let ok = 0, warn = 0, err = 0;
    let totalDivergence = 0;

    data.forEach(d => {
      if (d.status === "OK") ok++;
      if (d.status === "WARNING") warn++;
      if (d.status === "ERROR") err++;
      totalDivergence += Math.abs(d.difference); // absolute divergence sum
    });

    let filtered = data.filter(d => {
      if (statusFilter !== "ALL" && d.status !== statusFilter) return false;
      if (search && !d.ticker.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });

    filtered.sort((a, b) => {
      if (sortBy === "ticker") return a.ticker.localeCompare(b.ticker);
      if (sortBy === "difference") return Math.abs(b.difference) - Math.abs(a.difference); // desc
      if (sortBy === "percent") return Math.abs(b.difference_percent) - Math.abs(a.difference_percent); // desc
      return 0;
    });

    return { filteredData: filtered, kpis: { ok, warn, err, totalDivergence } };
  }, [data, search, statusFilter, sortBy]);

  return (
    <div className="space-y-6">
      
      {/* KPIs Section */}
      <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider mb-2">Resumo da Conciliação (Ledger vs Custódia)</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard
          title="Ativos Conciliados (OK)"
          value={isLoading ? "..." : kpis.ok.toString()}
          icon={CheckCircle}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="Avisos (Warning)"
          value={<span className={kpis.warn > 0 ? "text-[#f5a623]" : "text-white"}>{isLoading ? "..." : kpis.warn.toString()}</span>}
          icon={AlertTriangle}
          iconBgColor="bg-[#f5a623]/10"
          iconColor="text-[#f5a623]"
        />
        <WealthKpiCard
          title="Erros (Divergências)"
          value={<span className={kpis.err > 0 ? "text-[#e97070]" : "text-white"}>{isLoading ? "..." : kpis.err.toString()}</span>}
          icon={XCircle}
          iconBgColor="bg-[#e97070]/10"
          iconColor="text-[#e97070]"
        />
        <WealthKpiCard
          title="Volume de Divergência"
          value={<span className={kpis.totalDivergence > 0 ? "text-[#e97070]" : "text-white"}>{isLoading ? "..." : `${kpis.totalDivergence.toFixed(2)} quotas`}</span>}
          icon={Activity}
          iconBgColor="bg-neutral-800"
          iconColor="text-neutral-400"
        />
      </div>

      {/* Tabela Section */}
      <WealthChartCard title="Auditoria Inteligente de Posições" tableMode>
        
        {/* Controles */}
        <div className="p-4 border-b border-white/[0.05] flex flex-col md:flex-row gap-4 items-center justify-between bg-white/[0.02]">
          
          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
            <input 
              type="text" 
              placeholder="Buscar por ticker..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-neutral-900 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-neutral-500 focus:outline-none focus:border-[#4ecf98]/50"
            />
          </div>

          <div className="flex gap-2 w-full md:w-auto">
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="bg-neutral-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#4ecf98]/50 flex-1 md:flex-none"
            >
              <option value="ALL">Status: Todos</option>
              <option value="OK">Status: OK</option>
              <option value="WARNING">Status: Warning</option>
              <option value="ERROR">Status: Error</option>
            </select>

            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-neutral-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#4ecf98]/50 flex-1 md:flex-none"
            >
              <option value="difference">Ord: Dif Absoluta</option>
              <option value="percent">Ord: Dif %</option>
              <option value="ticker">Ord: Ticker</option>
            </select>
          </div>

        </div>

        {/* Tabela */}
        {isError ? (
          <div className="p-8 text-center text-red-400">Erro ao processar conciliação. Verifique a API.</div>
        ) : (
          <WealthTable
            data={filteredData}
            isLoading={isLoading}
            pageSize={10}
            emptyMessage="Nenhuma posição encontrada para os filtros atuais."
            columns={[
              { 
                header: "Ticker", 
                accessorKey: "ticker",
                className: "font-semibold text-white" 
              },
              { 
                header: "Corretora", 
                accessorKey: "broker",
                className: "text-neutral-400" 
              },
              { 
                header: "Ledger", 
                cell: (r) => r.ledger_quantity.toFixed(4),
                align: "right",
                className: "font-mono"
              },
              { 
                header: "Snapshot", 
                cell: (r) => r.snapshot_quantity.toFixed(4),
                align: "right",
                className: "font-mono"
              },
              { 
                header: "Diferença", 
                cell: (r) => {
                  const val = r.difference;
                  const sign = val > 0 ? "+" : "";
                  return `${sign}${val.toFixed(4)}`;
                },
                align: "right",
                className: (r) => r.difference === 0 ? "text-neutral-500 font-mono" : `${colorForValue(r.difference)} font-mono font-semibold`
              },
              { 
                header: "%", 
                cell: (r) => {
                  const val = r.difference_percent * 100;
                  const sign = val > 0 ? "+" : "";
                  return `${sign}${val.toFixed(2)}%`;
                },
                align: "right",
                className: (r) => r.difference_percent === 0 ? "text-neutral-500 font-mono" : `${colorForValue(r.difference_percent)} font-mono font-semibold`
              },
              {
                header: "Status",
                cell: (r) => {
                  if (r.status === "OK") return <span className="text-[#4ecf98] bg-[#4ecf98]/10 px-2 py-1 rounded text-xs font-medium">OK</span>;
                  if (r.status === "WARNING") return <span className="text-[#f5a623] bg-[#f5a623]/10 px-2 py-1 rounded text-xs font-medium">WARNING</span>;
                  return <span className="text-[#e97070] bg-[#e97070]/10 px-2 py-1 rounded text-xs font-medium">ERROR</span>;
                },
                align: "center"
              },
              { 
                header: "Ação Recomendada", 
                accessorKey: "recommendation",
                className: "text-xs text-neutral-400",
                align: "right"
              }
            ]}
          />
        )}
      </WealthChartCard>

    </div>
  );
}
