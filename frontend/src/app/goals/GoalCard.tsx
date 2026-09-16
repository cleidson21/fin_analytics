"use client";

import { useState } from "react";
import { GoalType, GoalStatus, GoalPriority, type Goal } from "./types";

// ------------------------------------------------------------------ //
// Utilitários de formatação                                           //
// ------------------------------------------------------------------ //

const BRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);

const GOAL_TYPE_LABELS: Record<string, string> = {
  EMERGENCY_RESERVE: "Reserva de Emergência",
  RETIREMENT: "Aposentadoria",
  TRAVEL: "Viagem",
  PURCHASE: "Compra",
  CUSTOM: "Personalizada",
  WEALTH_TARGET: "Patrimônio-Alvo",
  INVESTMENT_TARGET: "Investimento-Alvo",
  DIVIDEND_INCOME: "Renda de Dividendos",
  FINANCIAL_INDEPENDENCE: "Independência Financeira",
};

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  ACTIVE:    { label: "Ativa",     color: "#4ecf98", bg: "rgba(78,207,152,0.12)" },
  PAUSED:    { label: "Pausada",   color: "#f5a623", bg: "rgba(245,166,35,0.12)" },
  ACHIEVED:  { label: "Concluída", color: "#7EB8F7", bg: "rgba(126,184,247,0.12)" },
  CANCELLED: { label: "Cancelada", color: "#94a3b8", bg: "rgba(148,163,184,0.12)" },
};

const PRIORITY_CONFIG: Record<number, { label: string; color: string }> = {
  1: { label: "P1", color: "#ef4444" },
  2: { label: "P2", color: "#f97316" },
  3: { label: "P3", color: "#f5a623" },
  4: { label: "P4", color: "#7EB8F7" },
  5: { label: "P5", color: "#94a3b8" },
};

// ------------------------------------------------------------------ //
// GoalCard                                                            //
// ------------------------------------------------------------------ //

interface GoalCardProps {
  goal: Goal;
  onEdit: (goal: Goal) => void;
  onDelete: (goal: Goal) => void;
}

export function GoalCard({ goal, onEdit, onDelete }: GoalCardProps) {
  const status = STATUS_CONFIG[goal.status] ?? STATUS_CONFIG.ACTIVE;
  const priority = goal.priority ? PRIORITY_CONFIG[goal.priority] : null;
  const hasProgress =
    goal.current_amount !== null && goal.current_amount !== undefined;
  const progressPct = goal.progress_pct ?? 0;

  return (
    <div
      className="goal-card"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "16px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
        transition: "border-color 0.2s, background 0.2s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor =
          "rgba(255,255,255,0.16)";
        (e.currentTarget as HTMLDivElement).style.background =
          "rgba(255,255,255,0.05)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor =
          "rgba(255,255,255,0.08)";
        (e.currentTarget as HTMLDivElement).style.background =
          "rgba(255,255,255,0.03)";
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "2px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {GOAL_TYPE_LABELS[goal.goal_type] ?? goal.goal_type}
          </p>
          <h3 style={{ color: "#f1f5f9", fontWeight: 600, fontSize: "15px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {goal.name}
          </h3>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
          {priority && (
            <span
              style={{
                fontSize: "11px",
                fontWeight: 700,
                color: priority.color,
                background: `${priority.color}1a`,
                borderRadius: "6px",
                padding: "2px 7px",
              }}
            >
              {priority.label}
            </span>
          )}
          <span
            style={{
              fontSize: "11px",
              fontWeight: 500,
              color: status.color,
              background: status.bg,
              borderRadius: "6px",
              padding: "2px 8px",
            }}
          >
            {status.label}
          </span>
        </div>
      </div>

      {/* Valor Alvo */}
      <div>
        <p style={{ fontSize: "11px", color: "#64748b", marginBottom: "3px" }}>Valor Alvo</p>
        <p style={{ fontSize: "22px", fontWeight: 700, color: "#7EB8F7", letterSpacing: "-0.5px" }}>
          {BRL(goal.target_amount)}
        </p>
      </div>

      {/* Progresso */}
      {hasProgress ? (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>
              Atual: <span style={{ color: "#f1f5f9", fontWeight: 500 }}>
                {BRL(goal.current_amount!)}
              </span>
            </span>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "#4ecf98" }}>
              {progressPct.toFixed(1)}%
            </span>
          </div>
          <div style={{ height: "6px", background: "rgba(255,255,255,0.08)", borderRadius: "99px", overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                width: `${progressPct}%`,
                background: progressPct >= 100
                  ? "#4ecf98"
                  : progressPct >= 50
                  ? "linear-gradient(90deg, #7EB8F7, #4ecf98)"
                  : "#7EB8F7",
                borderRadius: "99px",
                transition: "width 0.4s ease",
              }}
            />
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ height: "6px", flex: 1, background: "rgba(255,255,255,0.06)", borderRadius: "99px" }} />
          <span style={{ fontSize: "11px", color: "#475569" }}>— sem valor atual</span>
        </div>
      )}

      {/* Info secundária */}
      <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
        {goal.target_date && (
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            📅 {new Date(goal.target_date + "T00:00:00").toLocaleDateString("pt-BR")}
          </span>
        )}
        {goal.monthly_contribution !== null && goal.monthly_contribution !== undefined && (
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            📈 {BRL(goal.monthly_contribution)}/mês
          </span>
        )}
      </div>

      {goal.description && (
        <p style={{ fontSize: "12px", color: "#64748b", lineHeight: 1.5, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "10px" }}>
          {goal.description}
        </p>
      )}

      {/* Ações */}
      <div style={{ display: "flex", gap: "8px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px" }}>
        <button
          onClick={() => onEdit(goal)}
          style={{
            flex: 1,
            padding: "7px",
            background: "rgba(126,184,247,0.08)",
            color: "#7EB8F7",
            border: "1px solid rgba(126,184,247,0.2)",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: 500,
            cursor: "pointer",
            transition: "background 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(126,184,247,0.16)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(126,184,247,0.08)")}
        >
          Editar
        </button>
        <button
          onClick={() => onDelete(goal)}
          style={{
            flex: 1,
            padding: "7px",
            background: "rgba(239,68,68,0.06)",
            color: "#f87171",
            border: "1px solid rgba(239,68,68,0.15)",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: 500,
            cursor: "pointer",
            transition: "background 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(239,68,68,0.14)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(239,68,68,0.06)")}
        >
          Excluir
        </button>
      </div>
    </div>
  );
}
