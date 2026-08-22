"use client";

import { useEffect, useState } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { Settings, Building2, CheckCircle2 } from "lucide-react";
import { fetchFromAPI } from "@/lib/api";

interface Account {
  provider: string;
  external_id: string;
  name: string;
  type: string;
  subtype?: string;
  bank?: string;
  connector?: string;
}

export default function SettingsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAccounts() {
      const data = await fetchFromAPI<Account[]>("/accounts");
      if (data) {
        setAccounts(data);
      }
      setLoading(false);
    }
    loadAccounts();
  }, []);

  return (
    <PageLayout title="Configurações">
      <div className="max-w-4xl mx-auto space-y-8 pb-12">
        <div className="flex items-center gap-4 border-b border-white/5 pb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 ring-1 ring-inset ring-indigo-500/20">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-zinc-100">Contas Conectadas</h1>
            <p className="text-zinc-500 mt-1 text-sm">Gerencie suas contas sincronizadas via Open Finance.</p>
          </div>
        </div>

        {loading ? (
          <div className="text-zinc-500 text-center py-12">Carregando contas...</div>
        ) : accounts.length === 0 ? (
          <div className="text-zinc-500 text-center py-12 bg-white/[0.02] rounded-2xl border border-white/5">
            Nenhuma conta conectada encontrada.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {accounts.map(acc => (
              <div key={`${acc.provider}-${acc.external_id}`} className="group relative overflow-hidden rounded-2xl bg-slate-900/40 p-6 border border-white/5 hover:border-indigo-500/30 transition-colors">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Building2 className="w-16 h-16 text-indigo-400" />
                </div>
                <div className="relative z-10">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3" /> Sincronizada
                    </span>
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-white/5 text-zinc-400 border border-white/10 uppercase tracking-wider">
                      {acc.provider}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-medium text-zinc-100 mb-1">{acc.name}</h3>
                  
                  <div className="space-y-1.5 mt-4 text-sm text-zinc-400">
                    <p className="flex justify-between border-b border-white/5 pb-1.5">
                      <span className="text-zinc-500">ID Externo</span>
                      <span className="font-mono text-xs">{acc.external_id}</span>
                    </p>
                    <p className="flex justify-between border-b border-white/5 pb-1.5">
                      <span className="text-zinc-500">Banco / Conector</span>
                      <span>{acc.bank || acc.connector || "N/A"}</span>
                    </p>
                    <p className="flex justify-between pb-1.5">
                      <span className="text-zinc-500">Tipo</span>
                      <span className="capitalize">{acc.type.toLowerCase()} {acc.subtype && `- ${acc.subtype}`}</span>
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
