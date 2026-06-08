import React, { useState, useEffect } from "react";
import { AdminEditDialog } from "./AdminEditDialog";
import { useDividendAdmin } from "@/hooks/useAdminCRUD";
import { Button } from "@/components/ui/button";

interface DividendEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  dividend: any;
  onSuccess: () => void;
}

export function DividendEditDialog({
  isOpen,
  onClose,
  dividend,
  onSuccess,
}: DividendEditDialogProps) {
  const { updateDividend, isUpdating } = useDividendAdmin();
  const [formData, setFormData] = useState({
    ticker: "",
    tipo_evento: "",
    observacao: "",
  });

  useEffect(() => {
    if (dividend) {
      setFormData({
        ticker: dividend.ticker || "",
        tipo_evento: dividend.tipo_evento || "",
        observacao: dividend.observacao || "",
      });
    }
  }, [dividend]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dividend) return;

    try {
      await updateDividend(dividend.id_economico, formData);
      alert("Dividendo atualizado com sucesso.\\nRegistro enviado para Audit Log.");
      onSuccess();
      onClose();
    } catch (error) {
      alert("Erro ao atualizar dividendo.");
    }
  };

  return (
    <AdminEditDialog isOpen={isOpen} onClose={onClose} title="Editar Dividendo">
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            ID Econômico
          </label>
          <input
            value={dividend?.id_economico || ""}
            disabled
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-400 cursor-not-allowed"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Ticker
          </label>
          <input
            name="ticker"
            value={formData.ticker}
            onChange={handleChange}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Tipo Evento
          </label>
          <input
            name="tipo_evento"
            value={formData.tipo_evento}
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
