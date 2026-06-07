"use client";

import React, { useState } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { AdminTable, ColumnDef } from "@/components/admin/AdminTable";
import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminFilters } from "@/components/admin/AdminFilters";
import { TransactionEditDialog } from "@/components/admin/TransactionEditDialog";
import { useTransactions } from "@/hooks/useTransactions";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Button } from "@/components/ui/button";

import Link from "next/link";

export default function TransactionsAdminPage() {
  const { isAdmin } = useCurrentUser();
  
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  
  // To avoid fetching on every keystroke, we use a separate state for the actual fetch
  const [activeSearch, setActiveSearch] = useState("");

  const { data, total, isLoading, refetch } = useTransactions({
    limit,
    offset,
    search: activeSearch,
  });

  const [editingTx, setEditingTx] = useState<any>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setActiveSearch(search);
  };

  const columns: ColumnDef<any>[] = [
    { key: "date", header: "Data" },
    { key: "description", header: "Descrição" },
    { key: "category", header: "Categoria" },
    { key: "natureza", header: "Natureza" },
    {
      key: "amount",
      header: "Valor",
      renderCell: (row) => {
        const val = parseFloat(row.amount);
        return (
          <span className={val < 0 ? "text-red-400" : "text-emerald-400"}>
            {new Intl.NumberFormat("pt-BR", {
              style: "currency",
              currency: "BRL",
            }).format(val)}
          </span>
        );
      },
    },
    { key: "account", header: "Conta" },
  ];

  if (isAdmin) {
    columns.push({
      key: "actions",
      header: "Ações",
      renderCell: (row) => (
        <Button
          variant="admin-outline"
          size="sm"
          onClick={() => setEditingTx(row)}
        >
          Editar
        </Button>
      ),
    });
  }

  return (
    <PageLayout
      title="Administração de Transações"
      subtitle="Gerencie e reclassifique transações no banco oficial"
      hideTitle={true}
      breadcrumb={
        <div className="text-sm font-medium text-zinc-500 flex items-center gap-2">
          <Link href="/governance" className="hover:text-white transition-colors">Governança</Link>
          <span>/</span>
          <span className="text-zinc-300">Transações</span>
        </div>
      }
    >
      <AdminFilters>
        <form onSubmit={handleSearch} className="flex w-full items-center space-x-2">
          <input
            type="text"
            placeholder="Buscar por descrição..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
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
        keyExtractor={(row) => row.id}
      />

      <AdminPagination
        total={total}
        limit={limit}
        offset={offset}
        onPageChange={setOffset}
      />

      <TransactionEditDialog
        isOpen={!!editingTx}
        onClose={() => setEditingTx(null)}
        transaction={editingTx}
        onSuccess={() => refetch()}
      />
    </PageLayout>
  );
}
