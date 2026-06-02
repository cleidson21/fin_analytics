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
