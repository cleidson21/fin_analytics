"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Filter, Pencil, ChevronLeft, ChevronRight, AlertTriangle, Loader2,
} from "lucide-react";
import { fetchFromAPI } from "@/lib/api";
import {
  TransactionGovernanceModal,
  type RawData,
  type GovernanceData,
  type AuditEvent,
} from "@/components/governance/TransactionGovernanceModal";

interface GovernanceTransaction {
  raw: RawData;
  governance: GovernanceData;
}

interface GovernanceListResponse {
  items: GovernanceTransaction[];
  total: number;
  page: number;
  page_size: number;
}

interface TransactionDetail {
  raw: RawData;
  governance: GovernanceData;
  history: AuditEvent[];
}

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleDateString("pt-BR"); }
  catch { return iso; }
}

function formatBRL(amount: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })
    .format(Math.abs(amount));
}

function getAmountColor(tx: GovernanceTransaction): string {
  if (tx.governance.governance_status === "PENDING") return "#64748b";
  switch (tx.governance.economic_classification) {
    case "ENTRADA": return "#22c55e";
    case "SAIDA":   return "#ef4444";
    default:         return "#64748b";
  }
}

const GOV_BADGE: Record<string, { label: string; bg: string; color: string }> = {
  ENTRADA:  { label: "ENTRADA",  bg: "rgba(34,197,94,0.15)",  color: "#22c55e" },
  SAIDA:    { label: "SAIDA",    bg: "rgba(239,68,68,0.15)",  color: "#ef4444" },
  IGNORAR:  { label: "IGNORAR",  bg: "rgba(245,158,11,0.15)", color: "#f59e0b" },
  PENDING:  { label: "PENDENTE", bg: "rgba(100,116,139,0.15)",color: "#64748b" },
};

function GovBadge({ tx }: { tx: GovernanceTransaction }) {
  const key = tx.governance.governance_status === "PENDING"
    ? "PENDING"
    : tx.governance.economic_classification || "PENDING";
  const b = GOV_BADGE[key] || GOV_BADGE.PENDING;
  return (
    <span style={{
      display: "inline-block", padding: "2px 10px", borderRadius: "99px",
      fontSize: "10px", fontWeight: 700, letterSpacing: "0.05em",
      background: b.bg, color: b.color, border: `1px solid ${b.color}30`,
    }}>
      {b.label}
    </span>
  );
}

const selectStyle: React.CSSProperties = {
  padding: "6px 10px", borderRadius: "7px", fontSize: "12px",
  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
  color: "#e2e8f0", outline: "none", cursor: "pointer",
};

const inputStyle: React.CSSProperties = {
  padding: "6px 10px", borderRadius: "7px", fontSize: "12px",
  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
  color: "#e2e8f0", outline: "none",
};

const paginationBtnStyle: React.CSSProperties = {
  padding: "5px 8px", borderRadius: "6px",
  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
  color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center",
};

const PAGE_SIZE = 30;

export function GovernanceClassificationsTab() {
  const [items, setItems] = useState<GovernanceTransaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterClassification, setFilterClassification] = useState("");
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterSortDir, setFilterSortDir] = useState("desc");
  const [loading, setLoading] = useState(false);
  const [modalTx, setModalTx] = useState<TransactionDetail | null>(null);
  const [loadingModal, setLoadingModal] = useState(false);

  const load = useCallback(async (p: number = page) => {
    setLoading(true);
    const params = new URLSearchParams();
    params.set("page", String(p));
    params.set("page_size", String(PAGE_SIZE));
    if (filterStatus) params.set("governance_status", filterStatus);
    if (filterClassification) params.set("economic_classification", filterClassification);
    if (filterStartDate) params.set("start_date", filterStartDate);
    if (filterEndDate) params.set("end_date", filterEndDate);
    if (filterCategory) params.set("category", filterCategory);
    params.set("sort_dir", filterSortDir);
    const data = await fetchFromAPI<GovernanceListResponse>(`/governance/transactions?${params.toString()}`);
    if (data) { setItems(data.items); setTotal(data.total); }
    setLoading(false);
  }, [page, filterStatus, filterClassification, filterStartDate, filterEndDate, filterCategory, filterSortDir]);

  useEffect(() => { load(1); setPage(1); }, [filterStatus, filterClassification, filterStartDate, filterEndDate, filterCategory, filterSortDir]);
  useEffect(() => { load(page); }, [page]);

  async function openModal(tx: GovernanceTransaction) {
    setLoadingModal(true);
    const detail = await fetchFromAPI<TransactionDetail>(`/governance/transactions/${tx.raw.provider}/${tx.raw.external_id}`);
    if (detail) setModalTx(detail);
    setLoadingModal(false);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pendingCount = items.filter(t => t.governance.governance_status === "PENDING").length;

  return (
    <div>
      {pendingCount > 0 && (
        <div style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", borderRadius: "10px", padding: "10px 16px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "10px" }}>
          <AlertTriangle size={16} color="#f59e0b" />
          <span style={{ color: "#fbbf24", fontSize: "13px" }}><strong>{pendingCount}</strong> transacoes nesta pagina aguardam classificacao.</span>
        </div>
      )}

      <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "14px 16px", marginBottom: "16px", display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "flex-end" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#64748b" }}>
          <Filter size={14} /> <span style={{ fontSize: "12px", fontWeight: 600 }}>Filtros</span>
        </div>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
          <option value="" className="bg-slate-900">Todos os status</option>
          <option value="PENDING" className="bg-slate-900">Pendentes</option>
          <option value="CLASSIFIED" className="bg-slate-900">Classificados</option>
        </select>
        <select value={filterClassification} onChange={e => setFilterClassification(e.target.value)} style={selectStyle}>
          <option value="" className="bg-slate-900">Toda classificacao</option>
          <option value="ENTRADA" className="bg-slate-900">Entrada</option>
          <option value="SAIDA" className="bg-slate-900">Saida</option>
          <option value="IGNORAR" className="bg-slate-900">Ignorar</option>
        </select>
        <select value={filterSortDir} onChange={e => setFilterSortDir(e.target.value)} style={selectStyle}>
          <option value="desc" className="bg-slate-900">Mais recentes primeiro</option>
          <option value="asc" className="bg-slate-900">Mais antigos primeiro</option>
        </select>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ color: "#64748b", fontSize: "11px" }}>De</span>
          <input type="date" value={filterStartDate} onChange={e => setFilterStartDate(e.target.value)} style={inputStyle} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ color: "#64748b", fontSize: "11px" }}>Ate</span>
          <input type="date" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} style={inputStyle} />
        </div>
        <button onClick={() => { setFilterStatus(""); setFilterClassification(""); setFilterStartDate(""); setFilterEndDate(""); setFilterCategory(""); }} style={{ padding: "6px 12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)", background: "transparent", color: "#64748b", fontSize: "11px", cursor: "pointer" }}>
          Limpar
        </button>
        <div style={{ marginLeft: "auto", color: "#64748b", fontSize: "12px" }}>{total} transacoes</div>
      </div>

      <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(0,0,0,0.2)" }}>
                {["Data", "Descricao", "Valor", "Categoria (API)", "Classificacao", "Investimento", ""].map(h => (
                  <th key={h} style={{ padding: "10px 14px", textAlign: "left", color: "#64748b", fontWeight: 600, fontSize: "11px", letterSpacing: "0.05em", whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
                  <Loader2 size={20} style={{ display: "inline", animation: "spin 1s linear infinite" }} /> Carregando...
                </td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={7} style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>Nenhuma transacao encontrada.</td></tr>
              ) : items.map((tx, i) => (
                <tr key={`${tx.raw.provider}/${tx.raw.external_id}`} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)", transition: "background 0.1s" }}>
                  <td style={{ padding: "10px 14px", color: "#94a3b8", whiteSpace: "nowrap" }}>{formatDate(tx.raw.date)}</td>
                  <td style={{ padding: "10px 14px", maxWidth: "220px" }}>
                    <div style={{ color: "#e2e8f0", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{tx.raw.description}</div>
                    {tx.raw.merchant_name && <div style={{ color: "#64748b", fontSize: "11px" }}>{tx.raw.merchant_name}</div>}
                  </td>
                  <td style={{ padding: "10px 14px", fontWeight: 700, whiteSpace: "nowrap", color: getAmountColor(tx) }}>
                    {formatBRL(tx.raw.amount)}
                  </td>
                  <td style={{ padding: "10px 14px", color: "#94a3b8", fontSize: "12px" }}>{tx.raw.category || "---"}</td>
                  <td style={{ padding: "10px 14px" }}><GovBadge tx={tx} /></td>
                  <td style={{ padding: "10px 14px", color: "#64748b", fontSize: "12px" }}>{tx.governance.investment_name || "---"}</td>
                  <td style={{ padding: "10px 14px", textAlign: "right" }}>
                    <button onClick={() => openModal(tx)} disabled={loadingModal} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "6px", color: "#818cf8", padding: "5px 10px", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", fontSize: "11px" }}>
                      <Pencil size={11} /> Classificar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "12px", padding: "12px 16px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={paginationBtnStyle}><ChevronLeft size={14} /></button>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#94a3b8", fontSize: "12px" }}>
              Página
              <input 
                type="number" 
                min={1} 
                max={totalPages} 
                value={page}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  if (!isNaN(val) && val >= 1 && val <= totalPages) {
                    setPage(val);
                  }
                }}
                style={{ ...inputStyle, width: "60px", textAlign: "center", padding: "4px" }}
              />
              de {totalPages}
            </div>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={paginationBtnStyle}><ChevronRight size={14} /></button>
          </div>
        )}
      </div>

      {modalTx && (
        <TransactionGovernanceModal
          raw={modalTx.raw}
          governance={modalTx.governance}
          history={modalTx.history}
          onClose={() => setModalTx(null)}
          onSaved={() => { setModalTx(null); load(page); }}
        />
      )}
    </div>
  );
}
