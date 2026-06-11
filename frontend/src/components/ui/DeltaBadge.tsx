import React from "react";
import { colorForValue } from "@/lib/utils";

interface DeltaBadgeProps {
  value: number;
  invertido?: boolean;
}

export function DeltaBadge({ value, invertido = false }: DeltaBadgeProps) {
  if (value === 0) {
    return (
      <span className="inline-flex rounded-full px-2 py-1 text-xs bg-white/5 text-neutral-500 font-medium border border-white/10">
        0.0%
      </span>
    );
  }

  const colorClass = colorForValue(value, invertido);
  const formattedValue = value > 0 ? `+${value.toFixed(1)}%` : `${value.toFixed(1)}%`;
  
  // Extrair a cor para o background dinâmico
  const isPositiveSemantic = invertido ? value < 0 : value > 0;
  
  // bg verde ou vermelho fraco com borda
  const bgClass = isPositiveSemantic 
    ? "bg-[#4ecf98]/10 border border-[#4ecf98]/20" 
    : "bg-[#e97070]/10 border border-[#e97070]/20";

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${bgClass} ${colorClass}`}>
      {formattedValue}
    </span>
  );
}
