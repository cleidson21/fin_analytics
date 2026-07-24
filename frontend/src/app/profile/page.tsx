"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { useAuth } from "@/contexts/AuthContext";
import { User, ShieldCheck } from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <PageLayout title="Perfil">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Painel do Perfil do Usuário */}
        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 bg-white/[0.02] border border-white/10 rounded-3xl p-8">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-400/10 text-emerald-300 ring-1 ring-inset ring-emerald-400/20">
            <User className="w-10 h-10" />
          </div>
          
          <div className="text-center w-full mt-4">
            <h2 className="text-2xl font-semibold text-zinc-100">{user?.name ?? "Usuário"}</h2>
            <p className="text-sm text-zinc-400 mt-1">{user?.email}</p>
            
            <div className="mt-6 flex flex-col gap-2 w-full max-w-xs mx-auto text-left">
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-xs text-zinc-500 uppercase tracking-wider">Papel</span>
                <span className="text-sm font-medium text-emerald-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  {user?.role}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-xs text-zinc-500 uppercase tracking-wider">ID</span>
                <span className="text-xs font-mono text-zinc-400 truncate max-w-[150px]">{user?.id}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-xs text-zinc-500 uppercase tracking-wider">Conta</span>
                <span className="text-sm text-zinc-300">{user?.is_active ? "Ativa" : "Inativa"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Painel de Progresso das Vertical Slices */}
        <div className="flex flex-col bg-white/[0.02] border border-white/10 rounded-3xl p-8">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
              <span className="text-xl">🚀</span> Progresso do Projeto
            </h2>
            <p className="text-sm text-zinc-400 mt-1">
              Acompanhamento da implementação técnica por Vertical Slices (E2E).
            </p>
          </div>

          <div className="flex flex-col gap-3 text-sm">
            {[
              { label: "VS-01 Autenticação", status: "done", desc: "Login, JWT (Access/Refresh), Sessão protegida" },
              { label: "VS-02 Contas", status: "done", desc: "GET /accounts real consumindo SQLite" },
              { label: "VS-03 Categorias", status: "pending", desc: "Fila para próxima iteração" },
              { label: "VS-04 Transações", status: "pending", desc: "Fila para próxima iteração" },
              { label: "VS-05 Providers", status: "pending", desc: "Fila para próxima iteração" },
              { label: "VS-10 Dashboard", status: "pending", desc: "Dashboard consolidado no layout restaurado" },
            ].map((item) => (
              <div
                key={item.label}
                className={`rounded-xl px-4 py-3 ring-1 ring-inset flex flex-col gap-1 ${
                  item.status === "done"
                    ? "bg-emerald-400/5 ring-emerald-400/20"
                    : "bg-white/[0.02] ring-white/10"
                }`}
              >
                <div className="flex items-center gap-2 font-medium">
                  {item.status === "done" ? "✅" : "⏳"} 
                  <span className={item.status === "done" ? "text-emerald-400" : "text-zinc-500"}>
                    {item.label}
                  </span>
                </div>
                <div className="text-xs text-zinc-500 ml-6">
                  {item.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
