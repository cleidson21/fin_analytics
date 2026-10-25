import React from "react";
interface DeltaBadgeProps {
  value: number;
  invertido?: boolean;
}

export function DeltaBadge({ value, invertido = false }: DeltaBadgeProps) {
  if (value === 0) {
    return (
      <span className="inline-flex rounded-full border border-border bg-muted/40 px-2 py-1 text-xs font-medium text-muted-foreground">
        0.0%
      </span>
    );
  }

  const formattedValue = value > 0 ? `+${value.toFixed(1)}%` : `${value.toFixed(1)}%`;
  
  // Extrair a cor para o background dinâmico
  const isPositiveSemantic = invertido ? value < 0 : value > 0;
  
  const toneClass = isPositiveSemantic
    ? "border border-financial-positive/25 bg-financial-positive/10 text-financial-positive"
    : "border border-financial-negative/25 bg-financial-negative/10 text-financial-negative";

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${toneClass}`}>
      {formattedValue}
    </span>
  );
}
