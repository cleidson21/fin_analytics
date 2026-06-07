export const CATEGORY_COLORS: Record<string, string> = {
  OUTROS: "#888780",
  ALIMENTACAO: "#7F77DD",
  TRANSPORTE: "#D85A30",
  MORADIA: "#1D9E75",
  FINANCAS: "#378ADD",
  COMPRAS: "#D4537E",
  SAUDE: "#EF9F27",
  ASSINATURAS: "#5DCAA5",
  LAZER: "#D4537E",
  PAGAMENTO_DIRETO: "#378ADD",
};

export const EXPENSE_PALETTE = [
  "#7F77DD", "#D85A30", "#1D9E75", "#378ADD",
  "#D4537E", "#EF9F27", "#5DCAA5", "#888780",
];

export function getCategoryColor(category: string, index: number): string {
  const key = category.toUpperCase().replace(/[\s-]+/g, "_");
  return CATEGORY_COLORS[key] ?? EXPENSE_PALETTE[index % EXPENSE_PALETTE.length];
}

export function getSemanticColor(className: string): string {
  const name = className.toLowerCase();
  // PT-BR first, EN fallback for backwards compatibility
  if (name.includes("renda fixa") || name.includes("fixed income")) return "#4ecf98";
  if (name.includes("ações") || name.includes("brazilian stocks") || name.includes("stock")) return "#7EB8F7";
  if (name.includes("fii") || name.includes("fundos imobili") || name.includes("real estate")) return "#7F77DD";
  if (name.includes("etf") || name.includes("exterior") || name.includes("global")) return "#f5a623";
  if (name.includes("cripto") || name.includes("crypto")) return "#e97070";
  if (name.includes("outros") || name.includes("others")) return "rgba(200,200,200,0.4)";
  return "rgba(255,255,255,0.15)";
}
