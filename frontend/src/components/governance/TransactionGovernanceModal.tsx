"use client";

import { useState } from "react";
import { X, ChevronDown, RotateCcw, Save, Loader2 } from "lucide-react";
import { fetchFromAPI } from "@/lib/api";

// ==========================================================================
// TYPES
// ==========================================================================

export interface RawData {
  provider: string;
  external_id: string;
  account_external_id: string;
  description: string;
  original_description?: string;
  category?: string;
  amount: number;
  currency: string;
  date: string;
  status: string;
  type: string;
  merchant_name?: string;
  receiver_name?: string;
  payer_name?: string;
}

export interface GovernanceData {
  governance_status: "PENDING" | "CLASSIFIED";
  economic_classification?: "ENTRADA" | "SAIDA" | "IGNORAR" | null;
  investment_name?: string | null;
  notes?: string | null;
  governed_at?: string | null;
}

export interface AuditEvent {
  id: number;
  action: "CREATE_CLASSIFICATION" | "UPDATE_CLASSIFICATION" | "ROLLBACK";
  before_json?: Record<string, unknown> | null;
  after_json?: Record<string, unknown> | null;
  changed_at: string;
  changed_by?: string | null;
  reason?: string | null;
}

interface Props {
  raw: RawData;
  governance: GovernanceData;
  history: AuditEvent[];
  onClose: () => void;
  onSaved: () => void;
}

// ==========================================================================
// HELPERS
// ==========================================================================

const ACTION_LABELS: Record<string, string> = {
  CREATE_CLASSIFICATION: "Classificado",
  UPDATE_CLASSIFICATION: "Alterado",
  ROLLBACK: "Rollback",
};

const ACTION_COLORS: Record<string, string> = {
  CREATE_CLASSIFICATION: "#22c55e",
  UPDATE_CLASSIFICATION: "#f59e0b",
  ROLLBACK: "#8b5cf6",
};

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "2-digit",
      hour: "2-digit", minute: "2-digit",
    });
  } catch { return iso; }
}

function formatAmount(amount: number, currency: string) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency", currency: currency || "BRL",
  }).format(amount);
}

function classificationSummary(json: Record<string, unknown> | null | undefined) {
  if (!json) return "—";
  const cls = json.economic_classification as string | null;
  const inv = json.investment_name as string | null;
  const st = json.governance_status as string;
  if (st === "PENDING") return "Pendente";
  if (!cls) return "—";
  return inv ? `${cls} / ${inv}` : cls;
}

// ==========================================================================
// BADGE COMPONENT
// ==========================================================================

function ClassificationBadge({ value }: { value?: string | null }) {
  const styles: Record<string, string> = {
    ENTRADA: "background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3)",
    SAIDA: "background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3)",
    IGNORAR: "background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3)",
  };
  const style = value ? styles[value] : "background:rgba(100,116,139,0.15);color:#94a3b8;border:1px solid rgba(100,116,139,0.3)";
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 10px",
      borderRadius: "99px",
      fontSize: "11px",
      fontWeight: 600,
      letterSpacing: "0.05em",
      cssText: style,
    } as React.CSSProperties}>
      {value || "PENDENTE"}
    </span>
  );
}

// ==========================================================================
// MAIN MODAL
// ==========================================================================

export function TransactionGovernanceModal({ raw, governance, history, onClose, onSaved }: Props) {
  const [classification, setClassification] = useState<"ENTRADA" | "SAIDA" | "IGNORAR" | "">(
    governance.economic_classification || ""
  );
  const [investmentName, setInvestmentName] = useState(governance.investment_name || "");
  const [notes, setNotes] = useState(governance.notes || "");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [rollingBack, setRollingBack] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!classification) {
      setError("Selecione uma classificação antes de salvar.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await fetchFromAPI(
        `/governance/transactions/${raw.provider}/${raw.external_id}/classify`,
        {
          method: "PATCH",
          body: JSON.stringify({
            economic_classification: classification,
            investment_name: investmentName || null,
            notes: notes || null,
            reason: reason || null,
          }),
        }
      );
      onSaved();
    } catch (e) {
      setError("Erro ao salvar. Tente novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRollback(auditId: number) {
    setRollingBack(auditId);
    setError(null);
    try {
      await fetchFromAPI(
        `/governance/transactions/${raw.provider}/${raw.external_id}/rollback/${auditId}?reason=Rollback+manual`,
        { method: "POST" }
      );
      onSaved();
    } catch (e) {
      setError("Erro ao reverter. Tente novamente.");
    } finally {
      setRollingBack(null);
    }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "16px",
    }}>
      <div style={{
        background: "#0f172a",
        border: "1px solid rgba(99,102,241,0.2)",
        borderRadius: "16px",
        width: "100%", maxWidth: "620px",
        maxHeight: "90vh",
        overflow: "hidden",
        display: "flex", flexDirection: "column",
        boxShadow: "0 25px 80px rgba(0,0,0,0.6)",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "20px 24px 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}>
          <div>
            <div style={{ color: "#e2e8f0", fontWeight: 700, fontSize: "15px" }}>
              Governança de Transação
            </div>
            <div style={{ color: "#64748b", fontSize: "11px", fontFamily: "monospace", marginTop: "2px" }}>
              {raw.provider} / {raw.external_id.slice(0, 16)}...
            </div>
          </div>
          <button onClick={onClose} style={{
            background: "rgba(255,255,255,0.05)", border: "none", borderRadius: "8px",
            width: "32px", height: "32px", cursor: "pointer", color: "#94a3b8",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <X size={16} />
          </button>
        </div>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {/* Section 1: Dados RAW */}
          <div style={{ padding: "20px 24px 0" }}>
            <div style={{ fontSize: "10px", color: "#6366f1", fontWeight: 700, letterSpacing: "0.1em", marginBottom: "12px" }}>
              DADOS ORIGINAIS — READONLY
            </div>
            <div style={{
              background: "rgba(255,255,255,0.03)", borderRadius: "10px",
              border: "1px solid rgba(255,255,255,0.05)",
              padding: "14px",
              display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px",
            }}>
              <div style={{ gridColumn: "1/-1" }}>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Descrição</span>
                <div style={{ color: "#e2e8f0", fontSize: "13px", fontWeight: 500, marginTop: "2px" }}>
                  {raw.description}
                </div>
              </div>
              <div>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Valor</span>
                <div style={{
                  color: raw.amount >= 0 ? "#22c55e" : "#ef4444",
                  fontSize: "16px", fontWeight: 700, marginTop: "2px",
                }}>
                  {formatAmount(raw.amount, raw.currency)}
                </div>
              </div>
              <div>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Data</span>
                <div style={{ color: "#e2e8f0", fontSize: "13px", marginTop: "2px" }}>
                  {raw.date ? new Date(raw.date).toLocaleDateString("pt-BR") : "—"}
                </div>
              </div>
              <div>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Categoria (API)</span>
                <div style={{ color: "#94a3b8", fontSize: "12px", marginTop: "2px" }}>{raw.category || "—"}</div>
              </div>
              <div>
                <span style={{ color: "#64748b", fontSize: "11px" }}>Tipo / Status</span>
                <div style={{ color: "#94a3b8", fontSize: "12px", marginTop: "2px" }}>
                  {raw.type} / {raw.status}
                </div>
              </div>
              {raw.merchant_name && (
                <div style={{ gridColumn: "1/-1" }}>
                  <span style={{ color: "#64748b", fontSize: "11px" }}>Estabelecimento</span>
                  <div style={{ color: "#94a3b8", fontSize: "12px", marginTop: "2px" }}>{raw.merchant_name}</div>
                </div>
              )}
            </div>
          </div>

          {/* Section 2: Governança */}
          <div style={{ padding: "20px 24px 0" }}>
            <div style={{ fontSize: "10px", color: "#6366f1", fontWeight: 700, letterSpacing: "0.1em", marginBottom: "12px" }}>
              GOVERNANÇA — EDITÁVEL
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {/* Classification selector */}
              <div>
                <label style={{ color: "#94a3b8", fontSize: "12px", display: "block", marginBottom: "8px" }}>
                  Classificação Econômica
                </label>
                <div style={{ display: "flex", gap: "8px" }}>
                  {(["ENTRADA", "SAIDA", "IGNORAR"] as const).map((opt) => {
                    const colors: Record<string, { active: string; border: string }> = {
                      ENTRADA: { active: "rgba(34,197,94,0.2)", border: "#22c55e" },
                      SAIDA: { active: "rgba(239,68,68,0.2)", border: "#ef4444" },
                      IGNORAR: { active: "rgba(245,158,11,0.2)", border: "#f59e0b" },
                    };
                    const isActive = classification === opt;
                    return (
                      <button key={opt} onClick={() => setClassification(opt)} style={{
                        flex: 1, padding: "10px 8px",
                        borderRadius: "8px", cursor: "pointer", fontWeight: 600, fontSize: "12px",
                        transition: "all 0.15s",
                        background: isActive ? colors[opt].active : "rgba(255,255,255,0.03)",
                        border: isActive ? `1.5px solid ${colors[opt].border}` : "1.5px solid rgba(255,255,255,0.08)",
                        color: isActive ? colors[opt].border : "#64748b",
                      }}>
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Investment name */}
              <div>
                <label style={{ color: "#94a3b8", fontSize: "12px", display: "block", marginBottom: "6px" }}>
                  Investimento <span style={{ color: "#475569", fontWeight: 400 }}>(texto livre, opcional)</span>
                </label>
                <input
                  value={investmentName}
                  onChange={(e) => setInvestmentName(e.target.value)}
                  placeholder="Ex: KNCR11, RDB 120% CDI, CDB XP..."
                  style={{
                    width: "100%", padding: "10px 12px", borderRadius: "8px",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                    color: "#e2e8f0", fontSize: "13px", outline: "none", boxSizing: "border-box",
                  }}
                />
              </div>

              {/* Notes */}
              <div>
                <label style={{ color: "#94a3b8", fontSize: "12px", display: "block", marginBottom: "6px" }}>
                  Observação
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Observação livre..."
                  rows={2}
                  style={{
                    width: "100%", padding: "10px 12px", borderRadius: "8px",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                    color: "#e2e8f0", fontSize: "13px", outline: "none", resize: "none",
                    boxSizing: "border-box", fontFamily: "inherit",
                  }}
                />
              </div>

              {/* Reason */}
              <div>
                <label style={{ color: "#94a3b8", fontSize: "12px", display: "block", marginBottom: "6px" }}>
                  Motivo da alteração <span style={{ color: "#475569", fontWeight: 400 }}>(opcional)</span>
                </label>
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Ex: Confirmado extrato Nubank..."
                  style={{
                    width: "100%", padding: "10px 12px", borderRadius: "8px",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                    color: "#e2e8f0", fontSize: "13px", outline: "none", boxSizing: "border-box",
                  }}
                />
              </div>

              {error && (
                <div style={{ color: "#f87171", fontSize: "12px", padding: "8px 12px", background: "rgba(239,68,68,0.1)", borderRadius: "6px" }}>
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Section 3: History */}
          {history.length > 0 && (
            <div style={{ padding: "20px 24px 0" }}>
              <div style={{ fontSize: "10px", color: "#6366f1", fontWeight: 700, letterSpacing: "0.1em", marginBottom: "12px" }}>
                HISTÓRICO DE EVENTOS DE GOVERNANÇA
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {history.map((ev) => (
                  <div key={ev.id} style={{
                    background: "rgba(255,255,255,0.02)",
                    border: "1px solid rgba(255,255,255,0.05)",
                    borderRadius: "8px", padding: "10px 12px",
                    display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px",
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "2px" }}>
                        <span style={{
                          fontSize: "10px", fontWeight: 700, letterSpacing: "0.05em",
                          color: ACTION_COLORS[ev.action] || "#94a3b8",
                        }}>
                          {ACTION_LABELS[ev.action] || ev.action}
                        </span>
                        <span style={{ color: "#475569", fontSize: "10px" }}>
                          {formatDate(ev.changed_at)}
                        </span>
                      </div>
                      <div style={{ color: "#64748b", fontSize: "11px" }}>
                        {classificationSummary(ev.before_json as Record<string, unknown>)} → {classificationSummary(ev.after_json as Record<string, unknown>)}
                      </div>
                      {ev.reason && (
                        <div style={{ color: "#475569", fontSize: "10px", marginTop: "2px", fontStyle: "italic" }}>
                          {ev.reason}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleRollback(ev.id)}
                      disabled={rollingBack === ev.id}
                      title="Restaurar estado ANTES desta mudança"
                      style={{
                        flexShrink: 0,
                        background: "rgba(139,92,246,0.1)", border: "1px solid rgba(139,92,246,0.2)",
                        borderRadius: "6px", color: "#8b5cf6",
                        padding: "5px 10px", fontSize: "11px", cursor: "pointer",
                        display: "flex", alignItems: "center", gap: "4px", whiteSpace: "nowrap",
                      }}
                    >
                      {rollingBack === ev.id ? <Loader2 size={11} className="animate-spin" /> : <RotateCcw size={11} />}
                      Restaurar antes
                    </button>
                  </div>
                ))}
              </div>
              <p style={{ color: "#475569", fontSize: "10px", marginTop: "8px", fontStyle: "italic" }}>
                "Restaurar antes" reverte ao estado que existia ANTES de cada evento. O rollback também é registrado no histórico.
              </p>
            </div>
          )}

          <div style={{ height: "24px" }} />
        </div>

        {/* Footer */}
        <div style={{
          padding: "16px 24px",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          display: "flex", gap: "10px", justifyContent: "flex-end",
        }}>
          <button onClick={onClose} style={{
            padding: "10px 20px", borderRadius: "8px",
            background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)",
            color: "#94a3b8", fontSize: "13px", cursor: "pointer", fontWeight: 500,
          }}>
            Cancelar
          </button>
          <button onClick={handleSave} disabled={saving} style={{
            padding: "10px 24px", borderRadius: "8px",
            background: saving ? "rgba(99,102,241,0.4)" : "rgba(99,102,241,0.9)",
            border: "none", color: "#fff", fontSize: "13px", cursor: saving ? "not-allowed" : "pointer",
            fontWeight: 600, display: "flex", alignItems: "center", gap: "6px",
            transition: "all 0.15s",
          }}>
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}
