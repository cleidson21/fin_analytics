"use client";

import { ChevronDown } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { getCategoryColor } from "@/lib/colors";

export interface InstallmentItem {
  purchase_id: string;
  base_name: string;
  original_name: string;
  date: string;
  installment_amount: number;
  current_installment: number;
  first_installment_found: number;
  total_installments: number;
  total_estimated: number;
  already_paid: number;
  remaining: number;
  projected_end_date: string | null; // data projetada de término (ex: 'Novembro 2026')
  is_active: boolean; // calculado no backend com regra de "sobrevivência no mês"
}

interface InstallmentCardProps {
  item: InstallmentItem;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

export function InstallmentCard({ item, index, isExpanded, onToggle }: InstallmentCardProps) {
  const isFinished = item.current_installment >= item.total_installments;
  const progress =
    item.total_installments > 0
      ? Math.min((item.current_installment / item.total_installments) * 100, 100)
      : 0;

  // Icon box color from palette
  const hexColor = getCategoryColor("", index);
  const iconBg = hexColor + "26"; // 15% opacity
  const initial = item.base_name.charAt(0).toUpperCase();

  // Projected end date from backend
  const projectedEnd = item.projected_end_date ?? "-";

  return (
    <article className="overflow-hidden rounded-xl border border-white/[0.07] bg-[#131313]">

      {/* ── Header — sempre visível ──────────────────────────────── */}
      <div
        role="button"
        tabIndex={0}
        onClick={onToggle}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onToggle(); }}
        className="flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-white/[0.02]"
        aria-expanded={isExpanded}
        id={`installment-card-${item.purchase_id}`}
      >
        {/* Icon box */}
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-[10px] text-lg font-semibold"
          style={{ background: iconBg, color: hexColor }}
        >
          {initial}
        </div>

        {/* Info central */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-white">{item.base_name}</p>
          <p className="text-xs text-neutral-500">
            {item.current_installment}/{item.total_installments}x · {formatCurrency(item.installment_amount)}/mês
          </p>
        </div>

        {/* Badge status */}
        <div className="flex shrink-0 items-center gap-2">
          {item.first_installment_found > 1 && (
            <span className="flex-shrink-0 rounded-full bg-[#f5a623]/10 px-2 py-0.5 text-[10px] text-[#f5a623]">
              Histórico parcial importado
            </span>
          )}
          {!isFinished ? (
            <span className="flex-shrink-0 rounded-full bg-green-500/10 px-2 py-0.5 text-[10px] text-green-400">
              Ativo
            </span>
          ) : (
            <span className="flex-shrink-0 rounded-full bg-white/[0.06] px-2 py-0.5 text-[10px] text-neutral-400">
              Finalizado
            </span>
          )}
        </div>

        {/* Valor restante */}
        <div className="flex-shrink-0 text-right">
          <p className="text-sm font-medium text-[#f5a623]">{formatCurrency(item.remaining)}</p>
          <p className="text-xs text-neutral-600">restante</p>
        </div>

        {/* Chevron */}
        <ChevronDown
          className={`ml-2 h-4 w-4 flex-shrink-0 text-neutral-600 transition-transform duration-300 ${isExpanded ? "rotate-180" : "rotate-0"}`}
        />
      </div>

      {/* ── Progress bar — sempre visível ────────────────────────── */}
      <div className="px-4 pb-3">
        <div className="h-[3px] overflow-hidden rounded-full bg-white/[0.04]">
          <div
            className="h-full rounded-full bg-[#4ecf98] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* ── Body — expansível ─────────────────────────────────────── */}
      <div
        className={`overflow-hidden transition-all duration-300 ${isExpanded ? "max-h-[700px] opacity-100" : "max-h-0 opacity-0"}`}
        aria-hidden={!isExpanded}
      >
        <div className="border-t border-white/[0.05] p-4">

          {/* Mini-stats */}
          <div className="mb-4 grid grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-xs uppercase tracking-widest text-neutral-600">Total</p>
              <p className="mt-1 text-sm font-medium text-white">{formatCurrency(item.total_estimated)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-neutral-600">Pago</p>
              <p className="mt-1 text-sm font-medium text-[#4ecf98]">{formatCurrency(item.already_paid)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-neutral-600">Restante</p>
              <p className="mt-1 text-sm font-medium text-[#f5a623]">{formatCurrency(item.remaining)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-neutral-600">Término</p>
              <p className="mt-1 text-sm font-medium text-white">{projectedEnd}</p>
            </div>
          </div>

          {/* Label de parcelas */}
          <p className="mb-2 text-xs text-neutral-600">
            Parcelas — {item.total_installments}x {formatCurrency(item.installment_amount)}/parcela
          </p>

          {/* Chips de parcelas */}
          <div className="flex flex-wrap gap-1">
            {Array.from({ length: item.total_installments }, (_, i) => {
              const num = i + 1;
              const isPaid = num <= item.current_installment;
              const isMissing = num < item.first_installment_found;

              if (isMissing) {
                return (
                  <span
                    key={`chip-${item.purchase_id}-${num}`}
                    className="inline-flex items-center gap-1 rounded-full bg-white/[0.03] px-2.5 py-1 text-[11px] font-medium text-neutral-500 opacity-70"
                  >
                    ✓ {num}/{item.total_installments} (inferida)
                  </span>
                );
              }

              return (
                <span
                  key={`chip-${item.purchase_id}-${num}`}
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium ${
                    isPaid
                      ? "bg-green-500/[0.08] text-green-500"
                      : "bg-white/[0.05] text-neutral-500"
                  }`}
                >
                  {isPaid ? "✓" : "○"} {num}/{item.total_installments}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </article>
  );
}
