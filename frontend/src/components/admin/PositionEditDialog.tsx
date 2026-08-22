import React, { useState, useEffect } from "react";
import { AdminEditDialog } from "./AdminEditDialog";
import { usePositionAdmin } from "@/hooks/useAdminCRUD";
import { Button } from "@/components/ui/button";
import { Position } from "@/types/entities";

interface PositionEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  position: Position;
  onSuccess: () => void;
}

export function PositionEditDialog({
  isOpen,
  onClose,
  position,
  onSuccess,
}: PositionEditDialogProps) {
  const { updatePosition, isUpdating } = usePositionAdmin();
  const [formData, setFormData] = useState({
    classe_ativo: "",
    observacao: "",
  });

  useEffect(() => {
    if (position) {
      setFormData({
        classe_ativo: position.classe_ativo || "",
        observacao: position.observacao || "",
      });
    }
  }, [position]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!position) return;

    try {
      await updatePosition(position.ticker ?? "", position.data_snapshot || position.snapshot_date || "", formData);

      alert("Posição atualizada com sucesso.\nRegistro enviado para Audit Log.");
      onSuccess();
      onClose();
    } catch {
      alert("Erro ao atualizar posição.");
    }
  };

  return (
    <AdminEditDialog isOpen={isOpen} onClose={onClose} title="Editar Posição">
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Ticker
          </label>
          <input
            value={position?.ticker || ""}
            disabled
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-400 cursor-not-allowed"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Data Snapshot
          </label>
          <input
            value={position?.data_snapshot || ""}
            disabled
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-400 cursor-not-allowed"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Classe Ativo
          </label>
          <input
            name="classe_ativo"
            value={formData.classe_ativo}
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
