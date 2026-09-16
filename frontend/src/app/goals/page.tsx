"use client";

import { useCallback, useEffect, useState } from "react";
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
    <PageLayout title="Metas" subtitle="Objetivos e marcos financeiros." hideTitle={true}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <p style={{ color: "#64748b", fontSize: "14px", margin: "4px 0 0" }}>
            {loading
              ? "Carregando..."
              : goals.length === 0
              ? "Nenhuma meta cadastrada"
              : `${goals.length} ${goals.length === 1 ? "meta" : "metas"}`}
          </p>
        </div>
        <button
          id="btn-create-goal"
          onClick={() => setShowCreate(true)}
          style={{
            padding: "10px 20px",
            background: "#7EB8F7",
            color: "#0f172a",
            border: "none",
            borderRadius: "10px",
            fontSize: "14px",
            fontWeight: 700,
            cursor: "pointer",
            transition: "opacity 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          + Nova Meta
        </button>
      </div>

      {/* Estado de erro */}
      {error && (
        <div
          style={{
            background: "rgba(239,68,68,0.08)",
            border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: "12px",
            padding: "16px 20px",
            color: "#f87171",
            fontSize: "14px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>{error}</span>
          <button
            onClick={loadGoals}
            style={{ color: "#f87171", background: "none", border: "none", cursor: "pointer", fontWeight: 600, fontSize: "13px" }}
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Estado de loading */}
      {loading && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: "16px",
                padding: "20px",
                height: "200px",
                animation: "pulse 1.5s ease-in-out infinite",
              }}
            />
          ))}
        </div>
      )}

      {/* Estado vazio */}
      {!loading && !error && goals.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "rgba(255,255,255,0.02)",
            border: "1px dashed rgba(255,255,255,0.08)",
            borderRadius: "20px",
          }}
        >
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>🎯</div>
          <h3 style={{ color: "#f1f5f9", fontSize: "18px", fontWeight: 600, margin: "0 0 8px" }}>
            Nenhuma meta cadastrada
          </h3>
          <p style={{ color: "#64748b", fontSize: "14px", margin: "0 0 24px" }}>
            Defina seus objetivos financeiros e acompanhe o progresso.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            style={{
              padding: "10px 24px",
              background: "#7EB8F7",
              color: "#0f172a",
              border: "none",
              borderRadius: "10px",
              fontSize: "14px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Criar Primeira Meta
          </button>
        </div>
      )}

      {/* Lista de metas */}
      {!loading && goals.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              onEdit={setEditingGoal}
              onDelete={setDeletingGoal}
            />
          ))}
        </div>
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

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </PageLayout>
  );
}
