"use client";

import React, { useState } from "react";
import { AdminTable, ColumnDef } from "@/components/admin/AdminTable";
import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminFilters } from "@/components/admin/AdminFilters";
import { CategoryMergeDialog } from "@/components/admin/CategoryMergeDialog";
import { useCategoriesAdmin } from "@/hooks/useCategoriesAdmin";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Button } from "@/components/ui/button";
import { AuthRequiredCard } from "@/components/ui/AuthRequiredCard";

export function CategoriesTab() {
  const { user, isAdmin, isViewer, isLoading: isAuthLoading } = useCurrentUser();
  
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  
  const [editingCategory, setEditingCategory] = useState<any>(null);

  const { data, total, isLoading, refetch } = useCategoriesAdmin({
    limit,
    offset,
    search: activeSearch,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setActiveSearch(searchInput);
  };

  const getRelevanceBadge = (count: number) => {
    if (count >= 100) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">Alta Utilização</span>;
    }
    if (count >= 10 && count <= 99) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">Uso Médio</span>;
    }
    if (count >= 2 && count <= 9) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">Baixo Uso</span>;
    }
    return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">Possível Duplicidade</span>;
  };

  const columns: ColumnDef<any>[] = [
    { key: "categoria", header: "Categoria" },
    { key: "quantidade_transacoes", header: "Qtd. Transações" },
    {
      key: "relevancia",
      header: "Indicador de Relevância",
      renderCell: (row) => getRelevanceBadge(row.quantidade_transacoes),
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
          onClick={() => setEditingCategory(row)}
          className="text-red-400 border-red-500/30 hover:bg-red-500/10"
        >
          Merge
        </Button>
      ),
    });
  }

  // --- Auth Checks ---
  if (isAuthLoading) {
    return <div className="text-zinc-400 p-8">Carregando permissões...</div>;
  }

  if (!user || (!isAdmin && !isViewer)) {
    return <div className="pt-8"><AuthRequiredCard title="Governança de Categorias" /></div>;
  }

  return (
    <div className="pt-4">
      <AdminFilters>
        <form onSubmit={handleSearch} className="flex flex-wrap w-full items-center gap-2">
          <input
            type="text"
            placeholder="Buscar nome da categoria..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="flex-1 min-w-[200px] rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
          <Button type="submit" variant="admin-outline">
            Buscar
          </Button>
        </form>
      </AdminFilters>

      <AdminTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        keyExtractor={(row) => row.categoria}
      />

      <AdminPagination
        total={total}
        limit={limit}
        offset={offset}
        onPageChange={setOffset}
      />

      {isAdmin && (
        <CategoryMergeDialog
          isOpen={!!editingCategory}
          onClose={() => setEditingCategory(null)}
          category={editingCategory}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  );
}
