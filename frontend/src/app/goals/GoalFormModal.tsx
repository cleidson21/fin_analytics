"use client";

import { useState, useEffect, useRef } from "react";
import type {
  Goal,
  GoalCreatePayload,
  GoalUpdatePayload,
  GoalType,
  GoalStatus,
} from "./types";
import { GOAL_TYPE_OPTIONS, GOAL_STATUS_OPTIONS } from "./types";

// ------------------------------------------------------------------ //
// Estilos inline reutilizáveis                                        //
// ------------------------------------------------------------------ //

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "9px 12px",
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: "8px",
  color: "#f1f5f9",
  fontSize: "14px",
  outline: "none",
  boxSizing: "border-box",
};

const labelStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#94a3b8",
  marginBottom: "5px",
  display: "block",
};

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
};

// ------------------------------------------------------------------ //
// GoalFormModal                                                       //
// ------------------------------------------------------------------ //

interface GoalFormModalProps {
  mode: "create" | "edit";
  goal?: Goal;
  onSave: (payload: GoalCreatePayload | GoalUpdatePayload) => Promise<void>;
  onClose: () => void;
  saving: boolean;
}

export function GoalFormModal({ mode, goal, onSave, onClose, saving }: GoalFormModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Campos do formulário
  const [name, setName] = useState(goal?.name ?? "");
  const [description, setDescription] = useState(goal?.description ?? "");
  const [goalType, setGoalType] = useState<GoalType>(goal?.goal_type ?? "CUSTOM");
  const [targetAmount, setTargetAmount] = useState(
    goal?.target_amount?.toString() ?? ""
  );
  const [targetDate, setTargetDate] = useState(goal?.target_date ?? "");
  const [currentAmount, setCurrentAmount] = useState(
    goal?.current_amount !== null && goal?.current_amount !== undefined
      ? goal.current_amount.toString()
      : ""
  );
  const [priority, setPriority] = useState(
    goal?.priority?.toString() ?? ""
  );
  const [monthlyContribution, setMonthlyContribution] = useState(
    goal?.monthly_contribution !== null && goal?.monthly_contribution !== undefined
      ? goal.monthly_contribution.toString()
      : ""
  );
  const [linkedAccountId, setLinkedAccountId] = useState(goal?.linked_account_id ?? "");
  const [status, setStatus] = useState<GoalStatus>(goal?.status ?? "ACTIVE");
  const [error, setError] = useState<string | null>(null);

  // Fechar ao clicar fora
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const targetAmountNum = parseFloat(targetAmount);
    if (!name || name.trim().length < 3) {
      setError("O nome deve ter pelo menos 3 caracteres.");
      return;
    }
    if (isNaN(targetAmountNum) || targetAmountNum <= 0) {
      setError("O valor alvo deve ser maior que zero.");
      return;
    }

    const payload: GoalCreatePayload | GoalUpdatePayload = {
      name: name.trim(),
      description: description.trim() || undefined,
      goal_type: goalType,
      target_amount: targetAmountNum,
      target_date: targetDate || undefined,
      current_amount: currentAmount !== "" ? parseFloat(currentAmount) : undefined,
      priority: priority !== "" ? parseInt(priority) : undefined,
      monthly_contribution: monthlyContribution !== "" ? parseFloat(monthlyContribution) : undefined,
      linked_account_id: linkedAccountId.trim() || undefined,
      ...(mode === "edit" ? { status } : {}),
    };

    try {
      await onSave(payload);
    } catch (err) {
      setError("Não foi possível salvar a meta. Tente novamente.");
    }
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.65)",
        backdropFilter: "blur(4px)",
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        style={{
          background: "#111111",
          border: "1px solid rgba(255,255,255,0.10)",
          borderRadius: "20px",
          padding: "28px",
          width: "100%",
          maxWidth: "560px",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 25px 60px rgba(0,0,0,0.6)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "22px" }}>
          <h2 style={{ color: "#f1f5f9", fontSize: "18px", fontWeight: 700, margin: 0 }}>
            {mode === "create" ? "Nova Meta" : "Editar Meta"}
          </h2>
          <button
            onClick={onClose}
            disabled={saving}
            style={{ color: "#64748b", background: "none", border: "none", cursor: "pointer", fontSize: "20px", lineHeight: 1, padding: "4px" }}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Nome */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Nome *</label>
            <input
              style={inputStyle}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Reserva de Emergência"
              maxLength={100}
              required
            />
          </div>

          {/* Tipo de meta */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Tipo de Meta *</label>
            <select
              style={{ ...inputStyle, appearance: "none" }}
              value={goalType}
              onChange={(e) => setGoalType(e.target.value as GoalType)}
              required
            >
              {GOAL_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} style={{ background: "#111" }}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Valor alvo */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Valor Alvo (R$) *</label>
            <input
              style={inputStyle}
              type="number"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
              placeholder="30000.00"
              min="0.01"
              step="0.01"
              required
            />
          </div>

          {/* Valor Atual */}
          <div style={fieldStyle}>
            <label style={labelStyle}>
              Valor Atual (R$)
              <span style={{ color: "#475569", marginLeft: "6px", fontWeight: 400 }}>
                — deixe em branco se não souber
              </span>
            </label>
            <input
              style={inputStyle}
              type="number"
              value={currentAmount}
              onChange={(e) => setCurrentAmount(e.target.value)}
              placeholder="—"
              min="0"
              step="0.01"
            />
          </div>

          {/* Linha: Prazo + Prioridade */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div style={fieldStyle}>
              <label style={labelStyle}>Prazo</label>
              <input
                style={inputStyle}
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>
            <div style={fieldStyle}>
              <label style={labelStyle}>Prioridade</label>
              <select
                style={{ ...inputStyle, appearance: "none" }}
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="" style={{ background: "#111" }}>— nenhuma</option>
                <option value="1" style={{ background: "#111" }}>1 — Muito Alta</option>
                <option value="2" style={{ background: "#111" }}>2 — Alta</option>
                <option value="3" style={{ background: "#111" }}>3 — Média</option>
                <option value="4" style={{ background: "#111" }}>4 — Baixa</option>
                <option value="5" style={{ background: "#111" }}>5 — Muito Baixa</option>
              </select>
            </div>
          </div>

          {/* Aporte Mensal */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Aporte Mensal Planejado (R$)</label>
            <input
              style={inputStyle}
              type="number"
              value={monthlyContribution}
              onChange={(e) => setMonthlyContribution(e.target.value)}
              placeholder="0.00"
              min="0"
              step="0.01"
            />
          </div>

          {/* Conta vinculada */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Conta / Carteira (referência)</label>
            <input
              style={inputStyle}
              value={linkedAccountId}
              onChange={(e) => setLinkedAccountId(e.target.value)}
              placeholder="Ex: NuInvest, XP, Corretora..."
              maxLength={255}
            />
          </div>

          {/* Descrição */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Descrição</label>
            <textarea
              style={{ ...inputStyle, minHeight: "72px", resize: "vertical" }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detalhes sobre esta meta..."
              maxLength={500}
            />
          </div>

          {/* Status (apenas em edição) */}
          {mode === "edit" && (
            <div style={fieldStyle}>
              <label style={labelStyle}>Status</label>
              <select
                style={{ ...inputStyle, appearance: "none" }}
                value={status}
                onChange={(e) => setStatus(e.target.value as GoalStatus)}
              >
                {GOAL_STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value} style={{ background: "#111" }}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {error && (
            <div style={{
              background: "rgba(239,68,68,0.10)",
              border: "1px solid rgba(239,68,68,0.25)",
              borderRadius: "8px",
              padding: "10px 14px",
              color: "#f87171",
              fontSize: "13px",
            }}>
              {error}
            </div>
          )}

          {/* Ações */}
          <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              style={{
                flex: 1,
                padding: "10px",
                background: "rgba(255,255,255,0.04)",
                color: "#94a3b8",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "10px",
                fontSize: "14px",
                cursor: "pointer",
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              style={{
                flex: 2,
                padding: "10px",
                background: saving ? "rgba(126,184,247,0.3)" : "#7EB8F7",
                color: "#0f172a",
                border: "none",
                borderRadius: "10px",
                fontSize: "14px",
                fontWeight: 700,
                cursor: saving ? "not-allowed" : "pointer",
                transition: "background 0.2s",
              }}
            >
              {saving ? "Salvando..." : mode === "create" ? "Criar Meta" : "Salvar Alterações"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ //
// ConfirmDialog — Modal de confirmação de exclusão                    //
// ------------------------------------------------------------------ //

interface ConfirmDialogProps {
  goal: Goal;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  deleting: boolean;
}

export function ConfirmDeleteDialog({ goal, onConfirm, onCancel, deleting }: ConfirmDialogProps) {
  return (
    <div
      onClick={onCancel}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.65)",
        backdropFilter: "blur(4px)",
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#111111",
          border: "1px solid rgba(239,68,68,0.25)",
          borderRadius: "16px",
          padding: "28px",
          width: "100%",
          maxWidth: "400px",
          boxShadow: "0 25px 60px rgba(0,0,0,0.6)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>⚠️</div>
          <h3 style={{ color: "#f1f5f9", fontSize: "17px", fontWeight: 700, margin: "0 0 8px" }}>
            Excluir Meta
          </h3>
          <p style={{ color: "#94a3b8", fontSize: "14px", margin: 0, lineHeight: 1.5 }}>
            Tem certeza que deseja excluir a meta{" "}
            <span style={{ color: "#f1f5f9", fontWeight: 500 }}>"{goal.name}"</span>?
            <br />
            Esta ação não pode ser desfeita.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={onCancel}
            disabled={deleting}
            style={{
              flex: 1,
              padding: "10px",
              background: "rgba(255,255,255,0.04)",
              color: "#94a3b8",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "10px",
              fontSize: "14px",
              cursor: "pointer",
            }}
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={deleting}
            style={{
              flex: 1,
              padding: "10px",
              background: deleting ? "rgba(239,68,68,0.3)" : "rgba(239,68,68,0.85)",
              color: "#fff",
              border: "none",
              borderRadius: "10px",
              fontSize: "14px",
              fontWeight: 700,
              cursor: deleting ? "not-allowed" : "pointer",
            }}
          >
            {deleting ? "Excluindo..." : "Excluir"}
          </button>
        </div>
      </div>
    </div>
  );
}
