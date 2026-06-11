"use client";

import { useEffect, useState } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";
import { Link as LinkIcon, Check, X, AlertCircle, ArrowRightLeft, FileQuestion } from "lucide-react";

interface RawEvent {
  id: string;
  source: string;
  event_type: string;
  event_date: string;
  amount_cents: number;
  metadata: Record<string, any>;
}

interface SuggestedLink {
  id: string;
  link_type: string;
  confidence: number;
  status: string;
  notes?: string;
  event_a: RawEvent;
  event_b: RawEvent;
}

interface ReconciliationInbox {
  suggestions: SuggestedLink[];
  orphans: RawEvent[];
}

export default function ReconciliationPage() {
  const [inbox, setInbox] = useState<ReconciliationInbox | null>(null);
  const [loading, setLoading] = useState(true);
  const [isUnauthorized, setIsUnauthorized] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadInbox = async () => {
    setLoading(true);
    try {
      const data = await fetchFromAPI<ReconciliationInbox>("/governance/reconciliations");
      setInbox(data);
    } catch (err) {
      if (err instanceof Error && err.name === "AuthError") {
        setIsUnauthorized(true);
      } else {
        console.error("Failed to load inbox", err);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInbox();
  }, []);

  const handleAction = async (linkId: string, action: "confirm" | "reject") => {
    setActionLoading(linkId);
    try {
      await fetchFromAPI(`/governance/links/${linkId}/${action}`, { method: "POST" });
      // Remove from suggestions locally to make it snappy
      setInbox((prev) => {
        if (!prev) return prev;
        const suggestion = prev.suggestions.find((s) => s.id === linkId);
        const newSuggestions = prev.suggestions.filter((s) => s.id !== linkId);
        // If rejected, the events become orphans again
        const newOrphans = [...prev.orphans];
        if (action === "reject" && suggestion) {
          newOrphans.push(suggestion.event_a);
          newOrphans.push(suggestion.event_b);
        }
        return { suggestions: newSuggestions, orphans: newOrphans };
      });
    } catch (err) {
      console.error(`Failed to ${action} link`, err);
    } finally {
      setActionLoading(null);
    }
  };

  if (isUnauthorized) {
    return <AuthRequiredCard title="Inbox de Reconciliação" />;
  }

  const formatCurrency = (cents: number) => {
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  };

  const getSourceColor = (source: string) => {
    if (source.includes("NUBANK")) return "text-purple-400 bg-purple-400/10 border-purple-400/20";
    if (source.includes("MYPROFIT") || source.includes("PIERRE")) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
    return "text-blue-400 bg-blue-400/10 border-blue-400/20";
  };

  return (
    <PageLayout title="Inbox de Reconciliação" subtitle="Aprove sugestões da Engine ou faça o match manual.">
      
      {/* KPIs */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center gap-3 text-zinc-400">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
            <span className="text-sm font-medium uppercase tracking-wider">Sugestões Pendentes</span>
          </div>
          <p className="mt-4 text-3xl font-semibold text-white">{inbox?.suggestions.length || 0}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center gap-3 text-zinc-400">
            <FileQuestion className="h-5 w-5 text-red-400" />
            <span className="text-sm font-medium uppercase tracking-wider">Eventos Órfãos</span>
          </div>
          <p className="mt-4 text-3xl font-semibold text-white">{inbox?.orphans.length || 0}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: Suggested Links */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
              <LinkIcon className="h-5 w-5 text-blue-400" />
              Sugestões da Engine
            </h3>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded-full text-zinc-300">
              {inbox?.suggestions.length || 0} Links
            </span>
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[1, 2].map((i) => (
                <div key={i} className="h-32 bg-white/5 rounded-xl"></div>
              ))}
            </div>
          ) : inbox?.suggestions.length === 0 ? (
            <div className="text-center p-8 bg-slate-900/50 border border-slate-800 rounded-xl">
              <Check className="h-8 w-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-zinc-400">Nenhuma sugestão pendente.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {inbox?.suggestions.map((suggestion) => (
                <div key={suggestion.id} className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 shadow-lg hover:border-slate-700 transition-colors">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-medium px-2 py-1 bg-blue-500/20 text-blue-300 rounded">
                      {suggestion.link_type}
                    </span>
                    <span className="text-xs text-zinc-500 font-mono">
                      Confiança: {(suggestion.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {/* Event A */}
                    <div className="flex-1 p-3 bg-black/40 rounded-lg border border-white/5">
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getSourceColor(suggestion.event_a.source)}`}>
                          {suggestion.event_a.source}
                        </span>
                        <span className="text-xs text-zinc-500">{suggestion.event_a.event_date}</span>
                      </div>
                      <p className="text-sm text-zinc-300 truncate" title={suggestion.event_a.metadata.descricao_original}>
                        {suggestion.event_a.metadata.descricao_original || 'S/ Descrição'}
                      </p>
                      <p className="text-sm font-semibold text-white mt-1">
                        {formatCurrency(suggestion.event_a.amount_cents)}
                      </p>
                    </div>

                    <ArrowRightLeft className="h-5 w-5 text-zinc-600 shrink-0" />

                    {/* Event B */}
                    <div className="flex-1 p-3 bg-black/40 rounded-lg border border-white/5">
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getSourceColor(suggestion.event_b.source)}`}>
                          {suggestion.event_b.source}
                        </span>
                        <span className="text-xs text-zinc-500">{suggestion.event_b.event_date}</span>
                      </div>
                      <p className="text-sm text-zinc-300 truncate" title={suggestion.event_b.metadata.descricao_original}>
                        {suggestion.event_b.metadata.descricao_original || 'S/ Descrição'}
                      </p>
                      <p className="text-sm font-semibold text-white mt-1">
                        {formatCurrency(suggestion.event_b.amount_cents)}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-4 flex gap-2 justify-end">
                    <Button 
                      variant="admin-ghost" 
                      size="sm" 
                      className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                      onClick={() => handleAction(suggestion.id, "reject")}
                      disabled={actionLoading === suggestion.id}
                    >
                      <X className="h-4 w-4 mr-1" /> Rejeitar
                    </Button>
                    <Button 
                      variant="admin" 
                      size="sm" 
                      className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border-none"
                      onClick={() => handleAction(suggestion.id, "confirm")}
                      disabled={actionLoading === suggestion.id}
                    >
                      <Check className="h-4 w-4 mr-1" /> Confirmar Match
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Right Column: Orphan Events */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
              <FileQuestion className="h-5 w-5 text-red-400" />
              Eventos Órfãos
            </h3>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded-full text-zinc-300">
              {inbox?.orphans.length || 0} Itens
            </span>
          </div>

          {loading ? (
             <div className="animate-pulse space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-white/5 rounded-xl"></div>
              ))}
           </div>
          ) : inbox?.orphans.length === 0 ? (
            <div className="text-center p-8 bg-slate-900/50 border border-slate-800 rounded-xl">
              <Check className="h-8 w-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-zinc-400">Todos os eventos possuem match!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {inbox?.orphans.map((orphan) => (
                <div key={orphan.id} className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 flex justify-between items-center hover:bg-slate-800 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getSourceColor(orphan.source)}`}>
                        {orphan.source}
                      </span>
                      <span className="text-xs text-zinc-500">{orphan.event_date}</span>
                    </div>
                    <p className="text-sm text-zinc-300">{orphan.metadata.descricao_original || orphan.event_type}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-white">{formatCurrency(orphan.amount_cents)}</p>
                    <p className="text-xs text-zinc-500 mt-1 cursor-pointer hover:text-white transition-colors">Ação manual</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </PageLayout>
  );
}
