"use client";

import React, { useState } from "react";
import { AdminTable, ColumnDef } from "@/components/admin/AdminTable";
import { AdminPagination } from "@/components/admin/AdminPagination";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useEvolucaoAdmin, Evolucao } from "@/hooks/useEvolucaoAdmin";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

export function EvolucaoTab() {
  const { user, isAdmin, isLoading: isAuthLoading } = useCurrentUser();
  
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const { data, total, isLoading } = useEvolucaoAdmin({
    limit,
    offset,
  });

  const columns: ColumnDef<Evolucao>[] = [
    { key: "reference_month", header: "Mês Ref." },
    { 
      key: "patrimonio", 
      header: "Patrimônio",
      renderCell: (row) => {
        const val = typeof row.patrimonio === 'number' ? row.patrimonio : parseFloat(String(row.patrimonio || "0"));
        return (
          <span className="font-medium text-emerald-400">
            {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)}
          </span>
        );
      },
    },
    {
      key: "pct_mensal",
      header: "% Mensal",
      renderCell: (row) => {
        if (row.pct_mensal === null) return <span>-</span>;
        const val = row.pct_mensal;
        return (
          <span className={val > 0 ? "text-emerald-400" : val < 0 ? "text-red-400" : "text-zinc-400"}>
            {(val * 100).toFixed(2)}%
          </span>
        );
      },
    },
    {
      key: "pct_acumulada",
      header: "% Acumulada",
      renderCell: (row) => {
        if (row.pct_acumulada === null) return <span>-</span>;
        const val = row.pct_acumulada;
        return (
          <span className={val > 0 ? "text-emerald-400" : val < 0 ? "text-red-400" : "text-zinc-400"}>
            {(val * 100).toFixed(2)}%
          </span>
        );
      },
    },
    {
      key: "compras",
      header: "Compras",
      renderCell: (row) => {
        if (row.compras === null) return <span>-</span>;
        return <span>{new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(row.compras)}</span>;
      },
    },
    {
      key: "vendas",
      header: "Vendas",
      renderCell: (row) => {
        if (row.vendas === null) return <span>-</span>;
        return <span>{new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(row.vendas)}</span>;
      },
    },
    {
      key: "proventos",
      header: "Proventos",
      renderCell: (row) => {
        if (row.proventos === null) return <span>-</span>;
        return <span className="text-emerald-400">{new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(row.proventos)}</span>;
      },
    },
    {
      key: "ibov_mensal",
      header: "IBOV Mensal",
      renderCell: (row) => {
        if (row.ibov_mensal === null) return <span>-</span>;
        return <span className="text-zinc-400">{(row.ibov_mensal * 100).toFixed(2)}%</span>;
      },
    },
  ];

  if (isAuthLoading) {
    return <div className="p-8 text-center text-zinc-400">Carregando...</div>;
  }

  if (!user) {
    return <AuthRequiredCard title="Você precisa estar logado para ver a Evolução Patrimonial." />;
  }

  return (
    <div className="space-y-6">


      <div className="rounded-xl border border-white/10 bg-slate-900/50 overflow-hidden shadow-xl">
        <AdminTable<Evolucao>
          columns={columns}
          data={data}
          isLoading={isLoading}
          keyExtractor={(item) => `${item.account_id}-${item.reference_month}`}
        />
        
        {!isLoading && total > 0 && (
          <div className="border-t border-white/10 p-4 bg-slate-900/80">
            <AdminPagination
              total={total}
              limit={limit}
              offset={offset}
              onPageChange={setOffset}
            />
          </div>
        )}
      </div>
    </div>
  );
}
