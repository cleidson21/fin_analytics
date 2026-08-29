"use client";

import React, { useState } from "react";
import { AdminTable, ColumnDef } from "@/components/admin/AdminTable";
import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminFilters } from "@/components/admin/AdminFilters";
import { PositionEditDialog } from "@/components/admin/PositionEditDialog";
import { Position } from "@/types/entities";
import { usePositionsAdmin } from "@/hooks/usePositionsAdmin";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Button } from "@/components/ui/button";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

export function PositionsTab() {
  const { user, isAdmin, isViewer, isLoading: isAuthLoading } = useCurrentUser();
  
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [tickerSearch, setTickerSearch] = useState("");
  const [classeAtivoSearch, setClasseAtivoSearch] = useState("");
  
  const [activeTicker, setActiveTicker] = useState("");
  const [activeClasseAtivo, setActiveClasseAtivo] = useState("");

  const { data, total, isLoading, refetch } = usePositionsAdmin({
    limit,
    offset,
    ticker: activeTicker,
    classe_ativo: activeClasseAtivo,
  });

  const [editingPos, setEditingPos] = useState<Position | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setActiveTicker(tickerSearch);
    setActiveClasseAtivo(classeAtivoSearch);
  };

  const columns: ColumnDef<Position>[] = [
    { key: "ticker", header: "Ticker" },
    { 
      key: "classe_ativo", 
      header: "Classe de Ativo",
      renderCell: (row) => <span>{row.classe_ativo || "-"}</span> 
    },
    { 
      key: "data_snapshot", 
      header: "Data Snapshot",
      renderCell: (row) => {
        if (!row.data_snapshot) return <span>-</span>;
        const parts = String(row.data_snapshot).split("-");
        if (parts.length === 3) return <span>{`${parts[2]}/${parts[1]}/${parts[0]}`}</span>;
        return <span>{row.data_snapshot}</span>;
      }
    },
    {
      key: "quantidade",
      header: "Quantidade",
      renderCell: (row) => {
        const val = typeof row.quantidade === 'number' ? row.quantidade : parseFloat(String(row.quantidade || "0"));
        return <span>{val.toFixed(2)}</span>;
      },
    },
    {
      key: "preco_medio",
      header: "Preço Médio",
      renderCell: (row) => {
        const val = typeof row.preco_medio === 'number' ? row.preco_medio : parseFloat(String(row.preco_medio || "0"));
        return (
          <span>
            {new Intl.NumberFormat("pt-BR", {
              style: "currency",
              currency: "BRL",
            }).format(val)}
          </span>
        );
      },
    },
    {
      key: "valor_investido",
      header: "Total Investido",
      renderCell: (row) => {
        const val = typeof row.valor_investido === 'number' ? row.valor_investido : parseFloat(String(row.valor_investido || "0"));
        return (
          <span>
            {val > 0 ? new Intl.NumberFormat("pt-BR", {
              style: "currency",
              currency: "BRL",
            }).format(val) : "-"}
          </span>
        );
      },
    },
    { key: "observacao", header: "Observação" },
  ];

  if (isAdmin) {
    columns.push({
      key: "actions",
      header: "Ações",
      renderCell: (row) => (
        <Button
          variant="admin-outline"
          size="sm"
          onClick={() => setEditingPos(row)}
        >
          Editar
        </Button>
      ),
    });
  }

  // --- Auth Checks ---
  if (isAuthLoading) {
    return <div className="text-zinc-400 p-8">Carregando permissões...</div>;
  }

  if (!user || (!isAdmin && !isViewer)) {
    return (
      <div className="mt-4">
        <AuthRequiredCard title="Administração de Posições" />
      </div>
    );
  }

  return (
    <div className="space-y-6 mt-4">
      <AdminFilters>
        <form onSubmit={handleSearch} className="flex w-full items-center space-x-2">
          <input
            type="text"
            placeholder="Buscar por Ticker..."
            value={tickerSearch}
            onChange={(e) => setTickerSearch(e.target.value)}
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
          <input
            type="text"
            placeholder="Classe de Ativo..."
            value={classeAtivoSearch}
            onChange={(e) => setClasseAtivoSearch(e.target.value)}
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
          <Button type="submit" variant="admin-outline">
            Filtrar
          </Button>
        </form>
      </AdminFilters>

      <AdminTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        keyExtractor={(row) => `${row.ticker}_${row.data_snapshot || row.snapshot_date}`}
      />

      <AdminPagination
        total={total}
        limit={limit}
        offset={offset}
        onPageChange={setOffset}
      />

      {isAdmin && editingPos && (
        <PositionEditDialog
          isOpen={true}
          onClose={() => setEditingPos(null)}
          position={editingPos}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  );
}
