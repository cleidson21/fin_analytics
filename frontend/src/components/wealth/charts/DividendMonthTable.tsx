"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { AssetMonthDetail, MonthlyAssetDetails } from "@/hooks/useDividendsData";
import { formatCurrency } from "@/lib/utils";
import Link from "next/link";

interface DividendMonthTableProps {
  monthlyAssetDetails: MonthlyAssetDetails;
  availableMonths: string[]; // sorted desc
}

const MONTH_NAMES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];

function formatMonthLabel(ym: string) {
  const [year, month] = ym.split("-");
  return `${MONTH_NAMES[parseInt(month) - 1]}/${year}`;
}

export function DividendMonthTable({ monthlyAssetDetails, availableMonths }: DividendMonthTableProps) {
  const [selectedMonth, setSelectedMonth] = useState<string>(availableMonths[0] ?? "");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const rows: AssetMonthDetail[] = selectedMonth
    ? (monthlyAssetDetails[selectedMonth] ?? [])
    : [];

  const totalRecebido = rows.reduce((s, r) => s + r.recebido, 0);

  if (availableMonths.length === 0) {
    return (
      <p className="text-sm text-zinc-500 py-6 text-center">Nenhum dado disponível.</p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Month selector */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-zinc-500">Mês</span>
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(v => !v)}
            className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-sm font-semibold text-zinc-200 hover:bg-white/[0.06] transition-colors"
          >
            {selectedMonth ? formatMonthLabel(selectedMonth) : "Selecionar"}
            <ChevronDown className={`h-3.5 w-3.5 text-zinc-500 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
          </button>

          {dropdownOpen && (
            <>
              {/* backdrop */}
              <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
              <div className="absolute left-0 top-full z-20 mt-1 max-h-56 w-36 overflow-y-auto rounded-xl border border-white/[0.09] bg-zinc-950/98 shadow-2xl shadow-black/60 backdrop-blur-xl">
                {availableMonths.map(m => (
                  <button
                    key={m}
                    onClick={() => { setSelectedMonth(m); setDropdownOpen(false); }}
                    className={`flex w-full items-center px-3 py-2 text-sm transition-colors ${
                      m === selectedMonth
                        ? "text-[#f5a623] bg-[#f5a623]/10 font-semibold"
                        : "text-zinc-300 hover:bg-white/[0.05]"
                    }`}
                  >
                    {formatMonthLabel(m)}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {selectedMonth && (
          <span className="ml-auto text-xs text-zinc-600">
            {rows.length} ativo{rows.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Table */}
      {rows.length === 0 ? (
        <p className="text-sm text-zinc-500 text-center py-6">
          Nenhum dado para {selectedMonth ? formatMonthLabel(selectedMonth) : "este mês"}.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl" style={{ border: "1px solid rgba(255,255,255,0.05)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}>
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Ativo</th>
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Recebido</th>
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-zinc-500">YOC</th>
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-zinc-500">DY</th>
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Cotas</th>
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-zinc-500">R$/cota</th>
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Part.</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => {
                const pct = totalRecebido > 0 ? (row.recebido / totalRecebido) * 100 : 0;
                return (
                  <tr
                    key={`${row.ticker}-${idx}`}
                    className="transition-colors hover:bg-white/[0.03]"
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}
                  >
                    {/* Ativo */}
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/wealth/asset/${row.ticker}`}
                          className="text-[#4ecf98] font-semibold hover:underline text-sm"
                        >
                          {row.ticker}
                        </Link>
                        {row.tipo_evento && (
                          <span className="rounded-md px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide"
                            style={{
                              background: row.tipo_evento === "DIVIDENDO" ? "#f5a62318" : row.tipo_evento === "JCP" ? "#e9707018" : "#4ecf9818",
                              color: row.tipo_evento === "DIVIDENDO" ? "#f5a623" : row.tipo_evento === "JCP" ? "#e97070" : "#4ecf98",
                            }}
                          >
                            {row.tipo_evento}
                          </span>
                        )}
                      </div>
                    </td>
                    {/* Recebido */}
                    <td className="px-4 py-2.5 text-right font-semibold text-[#f5a623]">
                      {formatCurrency(row.recebido)}
                    </td>
                    {/* YOC */}
                    <td className="px-4 py-2.5 text-right text-zinc-300">
                      {row.yoc != null ? `${(row.yoc * 100).toFixed(2)}%` : "—"}
                    </td>
                    {/* DY */}
                    <td className="px-4 py-2.5 text-right text-zinc-300">
                      {row.dy != null ? `${(row.dy * 100).toFixed(2)}%` : "—"}
                    </td>
                    {/* Cotas */}
                    <td className="px-4 py-2.5 text-right text-zinc-400">
                      {row.cotas > 0 ? row.cotas.toLocaleString("pt-BR", { maximumFractionDigits: 4 }) : "—"}
                    </td>
                    {/* R$/cota */}
                    <td className="px-4 py-2.5 text-right text-zinc-400">
                      {row.valor_por_cota > 0 ? formatCurrency(row.valor_por_cota) : "—"}
                    </td>
                    {/* Participação */}
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                          <div className="h-full rounded-full bg-[#4ecf98]" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs text-zinc-500 w-8 text-right">{pct.toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {/* Footer total */}
            <tfoot>
              <tr style={{ borderTop: "1px solid rgba(255,255,255,0.07)", background: "rgba(245,166,35,0.05)" }}>
                <td className="px-4 py-2.5 text-xs font-bold text-zinc-400 uppercase tracking-wide">Total</td>
                <td className="px-4 py-2.5 text-right text-sm font-bold text-[#f5a623]">
                  {formatCurrency(totalRecebido)}
                </td>
                <td colSpan={5} />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
