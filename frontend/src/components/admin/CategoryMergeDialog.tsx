import React, { useState } from "react";
import { AdminEditDialog } from "./AdminEditDialog";
import { useCategoryAdmin } from "@/hooks/useAdminCRUD";
import { Button } from "@/components/ui/button";

interface CategoryMergeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  category: any;
  onSuccess: () => void;
}

export function CategoryMergeDialog({
  isOpen,
  onClose,
  category,
  onSuccess,
}: CategoryMergeDialogProps) {
  const { mergeCategories, isMerging } = useCategoryAdmin();
  const [targetCategory, setTargetCategory] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!category || !targetCategory.trim()) return;

    // Phase 6 - Danger Zone Confirmation
    const isConfirmed = window.confirm(
      `ATENÇÃO: Você está prestes a mesclar:\n\n` +
      `[ ${category.categoria} ] ➔ [ ${targetCategory} ]\n\n` +
      `Isso afetará ${category.quantidade_transacoes} transações.\n` +
      `Esta operação não poderá ser desfeita. Confirmar Merge?`
    );

    if (!isConfirmed) return;

    try {
      await mergeCategories({
        source_category: category.categoria,
        target_category: targetCategory,
      });
      alert("Categorias mescladas com sucesso.\\nRegistro enviado para Audit Log.");
      onSuccess();
      onClose();
    } catch (error) {
      alert("Erro ao realizar o merge de categorias.");
    }
  };

  return (
    <AdminEditDialog isOpen={isOpen} onClose={onClose} title="Merge de Categoria">
      <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-md mb-4 text-sm font-medium">
        ATENÇÃO: esta operação não poderá ser desfeita. Todas as transações da categoria origem serão migradas para a categoria destino.
      </div>
      
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Categoria Origem
          </label>
          <div className="flex justify-between items-center w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-400 cursor-not-allowed">
            <span>{category?.categoria || ""}</span>
            <span className="text-xs bg-zinc-700 px-2 py-0.5 rounded-full">{category?.quantidade_transacoes} transações afetadas</span>
          </div>
        </div>

        <div className="flex justify-center text-zinc-500 py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-zinc-300">
            Categoria Destino (Nova ou Existente)
          </label>
          <input
            name="target_category"
            value={targetCategory}
            onChange={(e) => setTargetCategory(e.target.value)}
            required
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
            placeholder="Digite o nome da categoria destino..."
          />
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button type="button" variant="admin-outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" variant="admin" disabled={isMerging || !targetCategory.trim()} className="bg-red-600 hover:bg-red-700 text-white border-none">
            {isMerging ? "Mesclando..." : "Confirmar Merge"}
          </Button>
        </div>
      </form>
    </AdminEditDialog>
  );
}
