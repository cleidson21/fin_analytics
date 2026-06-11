import React, { useState, useEffect } from "react";
import { AdminEditDialog } from "./AdminEditDialog";
import { useTransactionAdmin } from "@/hooks/useAdminCRUD";
import { Button } from "@/components/ui/button";
import { Transaction } from "@/types/entities";

interface TransactionEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  transaction: Transaction;
  onSuccess: () => void;
}

export function TransactionEditDialog({
  isOpen,
  onClose,
  transaction,
  onSuccess,
}: TransactionEditDialogProps) {
  const { updateTransaction, isUpdating } = useTransactionAdmin();
  const [formData, setFormData] = useState({
    categoria: "",
    macro_categoria: "",
    parcelamento: "",
    observacao: "",
  });

  useEffect(() => {
    if (transaction) {
      setFormData({
        categoria: transaction.category || "",
        macro_categoria: transaction.macro_categoria || "",
        parcelamento: transaction.parcelamento || "",
        observacao: transaction.observacao || "",
      });
    }
  }, [transaction]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transaction) return;

    try {
      await updateTransaction(transaction.id, formData);
      // Simulate toast
      alert("Transação atualizada com sucesso.\nRegistro enviado para Audit Log.");
      onSuccess();
      onClose();
    } catch {
      alert("Erro ao atualizar transação.");
    }
  };

  return (
    <AdminEditDialog isOpen={isOpen} onClose={onClose} title="Editar Transação">
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Categoria (Macro)
          </label>
          <input
            name="macro_categoria"
            value={formData.macro_categoria}
            onChange={handleChange}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Sub Categoria
          </label>
          <input
            name="categoria"
            value={formData.categoria}
            onChange={handleChange}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Parcelamento
          </label>
          <input
            name="parcelamento"
            value={formData.parcelamento}
            onChange={handleChange}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Observação
          </label>
          <input
            name="observacao"
            value={formData.observacao}
            onChange={handleChange}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
        </div>
        <div className="flex justify-end space-x-2 pt-4">
          <Button type="button" variant="admin-outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" variant="admin" disabled={isUpdating}>
            {isUpdating ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </form>
    </AdminEditDialog>
  );
}
