"use client";

import React, { useState } from "react";
import { AdminTable, ColumnDef } from "@/components/admin/AdminTable";
import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminFilters } from "@/components/admin/AdminFilters";
import { DividendEditDialog } from "../admin/DividendEditDialog";
import { Dividend } from "@/types/entities";
import { useDividendsAdmin } from "@/hooks/useDividendsAdmin";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Button } from "@/components/ui/button";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

export function DividendsTab() {
  const { user, isAdmin, isViewer, isLoading: isAuthLoading } = useCurrentUser();
  
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [tickerSearch, setTickerSearch] = useState("");
  const [tipoEventoSearch, setTipoEventoSearch] = useState("");
  const [startDateSearch, setStartDateSearch] = useState("");
  const [endDateSearch, setEndDateSearch] = useState("");
  
  const [activeTicker, setActiveTicker] = useState("");
  const [activeTipoEvento, setActiveTipoEvento] = useState("");
  const [activeStartDate, setActiveStartDate] = useState("");
  const [activeEndDate, setActiveEndDate] = useState("");

  const { data, total, isLoading, refetch } = useDividendsAdmin({
    limit,
    offset,
    ticker: activeTicker,
    tipo_evento: activeTipoEvento,
    start_date: activeStartDate,
    end_date: activeEndDate,
  });

  const [editingDividend, setEditingDividend] = useState<Dividend | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setActiveTicker(tickerSearch);
    setActiveTipoEvento(tipoEventoSearch);
    setActiveStartDate(startDateSearch);
    setActiveEndDate(endDateSearch);
  };

  const columns: ColumnDef<Dividend>[] = [
    { key: "ticker", header: "Ticker" },
    { key: "tipo_evento", header: "Tipo Evento" },
    {
      key: "valor",
      header: "Valor",
      renderCell: (row) => {
        const val = typeof row.valor === 'number' ? row.valor : parseFloat(String(row.valor || "0"));
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
      key: "data_pagamento",
      header: "Data Pagamento",
      renderCell: (row) => {
        if (!row.data_pagamento) return <span>-</span>;
        // The format returned by API is usually YYYY-MM-DD
        const parts = row.data_pagamento.split("-");
        if (parts.length === 3) {
          return <span>{`${parts[2]}/${parts[1]}/${parts[0]}`}</span>;
        }
        return <span>{row.data_pagamento}</span>;
      },
    },
    {
      key: "observacao",
      header: "Observação",
      renderCell: (row) => <span>{row.observacao || "-"}</span>,
    },
  ];

  if (isAdmin) {
    columns.push({
      key: "actions",
      header: "Ações",
      renderCell: (row) => (
        <Button
          variant="admin-outline"
          size="sm"
          onClick={() => setEditingDividend(row)}
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
        <AuthRequiredCard title="Administração de Dividendos" />
      </div>
    );
  }

  return (
    <div className="space-y-6 mt-4">
      <AdminFilters>
        <form onSubmit={handleSearch} className="flex flex-wrap w-full items-center gap-2">
          <input
            type="text"
            placeholder="Buscar Ticker..."
            value={tickerSearch}
            onChange={(e) => setTickerSearch(e.target.value)}
            className="flex-1 min-w-[120px] rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
          <input
            type="text"
            placeholder="Tipo de Evento..."
            value={tipoEventoSearch}
            onChange={(e) => setTipoEventoSearch(e.target.value)}
            className="flex-1 min-w-[120px] rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
          <input
            type="date"
            title="Data Inicial"
            value={startDateSearch}
            onChange={(e) => setStartDateSearch(e.target.value)}
            className="w-32 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
          <input
            type="date"
            title="Data Final"
            value={endDateSearch}
            onChange={(e) => setEndDateSearch(e.target.value)}
            className="w-32 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
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
        keyExtractor={(row) => row.id ?? row.ticker ?? String(Math.random())}

      />

      <AdminPagination
        total={total}
        limit={limit}
        offset={offset}
        onPageChange={setOffset}
      />

      {isAdmin && editingDividend && (
        <DividendEditDialog
          isOpen={true}
          onClose={() => setEditingDividend(null)}
          dividend={editingDividend}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  );
}
