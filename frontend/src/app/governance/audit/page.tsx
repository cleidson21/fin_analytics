"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Clock, History, ShieldCheck, RefreshCcw, Loader2, ArrowUpRight } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";

// ==========================================================================
// TYPES — baseados em AuditEventOut do backend governance_router.py
// ==========================================================================

interface AuditEvent {
  id: number;
  provider: string;
  external_id: string;
  action: string;
  changed_at: string;
  reason: string | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
}

// ==========================================================================
// HELPERS
// ==========================================================================

type ActionFilter = "ALL" | "CREATE_CLASSIFICATION" | "UPDATE_CLASSIFICATION" | "ROLLBACK";

const ACTION_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  CREATE_CLASSIFICATION: { label: "Classificado", color: "#22c55e", bg: "rgba(34,197,94,0.12)" },
  UPDATE_CLASSIFICATION: { label: "Atualizado",   color: "#818cf8", bg: "rgba(99,102,241,0.12)" },
  ROLLBACK:              { label: "Rollback",      color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
};

function ActionBadge({ action }: { action: string }) {
  const cfg = ACTION_LABELS[action] || { label: action, color: "#64748b", bg: "rgba(100,116,139,0.12)" };
  return (
    <span style={{
      display: "inline-block", padding: "2px 10px", borderRadius: "99px",
      fontSize: "10px", fontWeight: 700, letterSpacing: "0.05em",
      color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.color}30`,
    }}>
      {cfg.label}
    </span>
  );
}

function fmt(iso: string) {
  try { return new Date(iso).toLocaleString("pt-BR"); }
  catch { return iso; }
}

function ClassificationValue({ json }: { json: Record<string, unknown> | null }) {
  if (!json) return <span style={{ color: "#64748b" }}>—</span>;
  const cls = json.economic_classification as string | undefined;
  const status = json.governance_status as string | undefined;
  if (!cls && !status) return <span style={{ color: "#64748b" }}>—</span>;
  const colors: Record<string, string> = { ENTRADA: "#22c55e", SAIDA: "#ef4444", IGNORAR: "#f59e0b" };
  return (
    <span style={{ color: colors[cls ?? ""] || "#94a3b8", fontSize: "12px", fontWeight: 600 }}>
      {cls || status}
    </span>
  );
}

// ==========================================================================
// PAGE
// ==========================================================================

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<ActionFilter>("ALL");

  async function load(f: ActionFilter = filter) {
    setLoading(true);
    const params = new URLSearchParams({ limit: "200" });
    if (f !== "ALL") params.set("action", f);
    const data = await fetchFromAPI<AuditEvent[]>(`/governance/audit-log?${params.toString()}`);
    if (data) setEvents(data);
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  function handleFilter(f: ActionFilter) {
    setFilter(f);
    load(f);
  }

  const FILTERS: { id: ActionFilter; label: string }[] = [
    { id: "ALL", label: "Todos" },
    { id: "CREATE_CLASSIFICATION", label: "Classificados" },
    { id: "UPDATE_CLASSIFICATION", label: "Atualizados" },
    { id: "ROLLBACK", label: "Rollbacks" },
  ];

  return (
    <PageLayout title="Auditoria" hideTitle={true}>

      {/* Header */}
      <div className="mb-6 flex items-center justify-between gap-3 flex-wrap">
        <div>
          <p className="text-zinc-500 text-sm">
            Historico imutavel de decisoes de governanca. Cada classificacao, atualizacao e rollback fica registrado.
          </p>
        </div>
        <Button variant="admin-outline" size="sm" onClick={() => load(filter)} disabled={loading}
          className="text-zinc-300 border-white/10 hover:bg-white/5">
          <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Atualizar
        </Button>
      </div>

      {/* Filter tabs */}
      <div style={{
        display: "flex", gap: "4px", marginBottom: "20px",
        background: "rgba(255,255,255,0.03)", borderRadius: "10px", padding: "4px",
        width: "fit-content", border: "1px solid rgba(255,255,255,0.06)",
      }}>
        {FILTERS.map(f => (
          <button key={f.id} onClick={() => handleFilter(f.id)} style={{
            padding: "7px 16px", borderRadius: "7px", fontSize: "12px",
            background: filter === f.id ? "rgba(99,102,241,0.2)" : "transparent",
            border: filter === f.id ? "1px solid rgba(99,102,241,0.3)" : "1px solid transparent",
            color: filter === f.id ? "#818cf8" : "#64748b",
            fontWeight: filter === f.id ? 600 : 400, cursor: "pointer", transition: "all 0.15s",
          }}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-16 text-zinc-500">
          <Loader2 className="inline animate-spin mr-2" size={16} /> Carregando...
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-16 text-zinc-500">
          <ShieldCheck className="mx-auto mb-3 h-8 w-8 text-zinc-600" />
          <p className="text-sm">Nenhum evento de governança encontrado.</p>
          <p className="text-xs mt-1">Classifique transações em <Link href="/governance/classify" className="text-indigo-400 hover:text-indigo-300">Governança / Pierre Finance</Link></p>
        </div>
      ) : (
        <div style={{
          background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: "12px", overflow: "hidden",
        }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(0,0,0,0.2)" }}>
                  {["Data/Hora", "Acao", "Descricao da transacao", "Antes", "Depois", "Motivo", ""].map(h => (
                    <th key={h} style={{
                      padding: "10px 14px", textAlign: "left", color: "#64748b",
                      fontWeight: 600, fontSize: "11px", letterSpacing: "0.05em", whiteSpace: "nowrap",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.map((ev, i) => (
                  <tr key={ev.id} style={{
                    borderBottom: "1px solid rgba(255,255,255,0.04)",
                    background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                  }}>
                    <td style={{ padding: "10px 14px", color: "#94a3b8", whiteSpace: "nowrap" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <Clock size={12} color="#64748b" />
                        {fmt(ev.changed_at)}
                      </div>
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <ActionBadge action={ev.action} />
                    </td>
                    <td style={{ padding: "10px 14px", maxWidth: "180px" }}>
                      <div style={{ color: "#e2e8f0", fontSize: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {(ev.after_json?.description as string) || (ev.before_json?.description as string) || ev.external_id}
                      </div>
                      <div style={{ color: "#475569", fontSize: "10px" }}>{ev.provider}</div>
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <ClassificationValue json={ev.before_json} />
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <ClassificationValue json={ev.after_json} />
                    </td>
                    <td style={{ padding: "10px 14px", color: "#64748b", fontSize: "11px", maxWidth: "140px" }}>
                      <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {ev.reason || "—"}
                      </span>
                    </td>
                    <td style={{ padding: "10px 14px", textAlign: "right" }}>
                      <Link
                        href={`/governance/classify`}
                        style={{
                          display: "inline-flex", alignItems: "center", gap: "4px",
                          fontSize: "11px", color: "#64748b",
                        }}
                        title="Ver transacao"
                      >
                        <ArrowUpRight size={13} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{
            padding: "10px 16px", borderTop: "1px solid rgba(255,255,255,0.06)",
            color: "#475569", fontSize: "11px", display: "flex", alignItems: "center", gap: "6px",
          }}>
            <History size={12} />
            {events.length} evento{events.length !== 1 ? "s" : ""} exibido{events.length !== 1 ? "s" : ""} &mdash; limite de 200 mais recentes
          </div>
        </div>
      )}
    </PageLayout>
  );
}
