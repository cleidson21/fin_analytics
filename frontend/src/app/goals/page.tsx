"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw, Target } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { GoalCard } from "./GoalCard";
import { GoalFormModal, ConfirmDeleteDialog } from "./GoalFormModal";
import type { Goal, GoalCreatePayload, GoalUpdatePayload } from "./types";

// ------------------------------------------------------------------ //
// Página de Metas                                                     //
// ------------------------------------------------------------------ //

export default function GoalsPage() {
  // ---- Estado principal ----
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ---- Modais ----
  const [showCreate, setShowCreate] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [deletingGoal, setDeletingGoal] = useState<Goal | null>(null);

  // ---- Estados de operação ----
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // ---------------------------------------------------------------- //
  // Load                                                              //
  // ---------------------------------------------------------------- //

  const loadGoals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFromAPI<Goal[]>("/goals");
      setGoals(data ?? []);
    } catch {
      setError("Não foi possível carregar as metas.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  // ---------------------------------------------------------------- //
  // Create                                                            //
  // ---------------------------------------------------------------- //

  const handleCreate = async (payload: GoalCreatePayload | GoalUpdatePayload) => {
    setSaving(true);
    try {
      await fetchFromAPI("/goals", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setShowCreate(false);
      await loadGoals();
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------- //
  // Update                                                            //
  // ---------------------------------------------------------------- //

  const handleUpdate = async (payload: GoalCreatePayload | GoalUpdatePayload) => {
    if (!editingGoal) return;
    setSaving(true);
    try {
      await fetchFromAPI(`/goals/${editingGoal.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setEditingGoal(null);
      await loadGoals();
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------- //
  // Delete                                                            //
  // ---------------------------------------------------------------- //

  const handleDelete = async () => {
    if (!deletingGoal) return;
    setDeleting(true);
    try {
      await fetchFromAPI(`/goals/${deletingGoal.id}`, {
        method: "DELETE",
      });
      setDeletingGoal(null);
      await loadGoals();
    } finally {
      setDeleting(false);
    }
  };

  // ---------------------------------------------------------------- //
  // Render                                                            //
  // ---------------------------------------------------------------- //

  return (
    <PageLayout title="Metas" subtitle="" hideTitle>
      <main className="mx-auto w-full max-w-6xl space-y-4 py-2">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-sky-700 dark:text-sky-300">Metas</p>
          <h1 className="mt-1 text-lg font-semibold tracking-tight text-foreground">Seus objetivos financeiros</h1>
          <p className="mt-0.5 text-xs text-muted-foreground" aria-live="polite">
            {loading ? "Carregando…" : goals.length === 0 ? "Nenhuma meta cadastrada" : `${goals.length} ${goals.length === 1 ? "meta" : "metas"}`}
          </p>
        </div>
        <button
          id="btn-create-goal"
          type="button"
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-sky-300 px-4 py-2.5 text-sm font-semibold text-zinc-950 transition hover:bg-sky-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/50"
        >
          <Plus aria-hidden="true" className="size-4" />
          Nova meta
        </button>
      </header>

      {error && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.055] px-4 py-3 text-sm text-destructive">
          <span>{error}</span>
          <button
            type="button"
            onClick={loadGoals}
            className="inline-flex items-center gap-2 rounded-lg px-2 py-1 text-xs font-semibold text-destructive hover:bg-rose-300/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-300/50"
          >
            <RefreshCw aria-hidden="true" className="size-3.5" />
            Tentar novamente
          </button>
        </div>
      )}

      {loading && (
        <div aria-label="Carregando metas" className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              aria-hidden="true"
              className="h-56 animate-pulse rounded-2xl border border-border bg-muted/30 motion-reduce:animate-none"
            />
          ))}
        </div>
      )}

      {!loading && !error && goals.length === 0 && (
        <section className="grid min-h-64 place-items-center rounded-2xl border border-dashed border-border bg-muted/25 px-6 py-10 text-center">
          <div>
          <span className="mx-auto grid size-11 place-items-center rounded-xl bg-sky-300/10 text-sky-700 dark:text-sky-300"><Target aria-hidden="true" className="size-5" /></span>
          <h2 className="mt-4 text-base font-semibold text-foreground">
            Nenhuma meta cadastrada
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Cadastre um objetivo para começar a acompanhar seu progresso.
          </p>
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="mt-5 rounded-xl bg-sky-300 px-4 py-2.5 text-sm font-semibold text-zinc-950 hover:bg-sky-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/50"
          >
            Criar primeira meta
          </button>
          </div>
        </section>
      )}

      {!loading && goals.length > 0 && (
        <section aria-label="Metas cadastradas" className="grid gap-4">
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              onEdit={setEditingGoal}
              onDelete={setDeletingGoal}
            />
          ))}
        </section>
      )}

      {/* Modal de criação */}
      {showCreate && (
        <GoalFormModal
          mode="create"
          onSave={handleCreate}
          onClose={() => setShowCreate(false)}
          saving={saving}
        />
      )}

      {/* Modal de edição */}
      {editingGoal && (
        <GoalFormModal
          mode="edit"
          goal={editingGoal}
          onSave={handleUpdate}
          onClose={() => setEditingGoal(null)}
          saving={saving}
        />
      )}

      {/* Confirmação de exclusão */}
      {deletingGoal && (
        <ConfirmDeleteDialog
          goal={deletingGoal}
          onConfirm={handleDelete}
          onCancel={() => setDeletingGoal(null)}
          deleting={deleting}
        />
      )}
      </main>
    </PageLayout>
  );
}
