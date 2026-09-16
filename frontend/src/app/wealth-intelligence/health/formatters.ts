export function formatCurrency(value: string | null) {
  if (value === null) return "—";

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value));
}

export function formatPercent(value: string | null) {
  if (value === null) return "—";

  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function formatPercentagePoints(value: string | null) {
  if (value === null) return "—";

  const formatted = new Intl.NumberFormat("pt-BR", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
  return `${formatted.replace("%", "").trim()} p.p.`;
}

function withPositiveSign(value: string, rawValue: string) {
  return Number(rawValue) > 0 ? `+${value}` : value;
}

export function formatSignedCurrency(value: string | null) {
  if (value === null) return "—";
  return withPositiveSign(formatCurrency(value), value);
}

export function formatSignedPercent(value: string | null) {
  if (value === null) return "—";
  return withPositiveSign(formatPercent(value), value);
}

export function formatSignedPercentagePoints(value: string | null) {
  if (value === null) return "—";
  return withPositiveSign(formatPercentagePoints(value), value);
}

export function formatRatio(value: string | null) {
  if (value === null) return "—";

  return `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value))}x`;
}

export function formatReferenceMonth(referenceMonth: string, short = false) {
  const [year, month] = referenceMonth.split("-").map(Number);
  const formatted = new Intl.DateTimeFormat("pt-BR", {
    month: short ? "short" : "long",
    year: "numeric",
  }).format(new Date(year, month - 1, 1));

  return short ? formatted.replace(" de ", "/").replace(".", "") : formatted;
}

export function formatCompactMonth(referenceMonth: string) {
  const [year, month] = referenceMonth.split("-").map(Number);
  const monthLabel = new Intl.DateTimeFormat("pt-BR", { month: "short" })
    .format(new Date(year, month - 1, 1))
    .replace(".", "");
  return `${monthLabel}/${String(year).slice(-2)}`;
}

export function financialTone(value: string | null) {
  if (value === null) return "text-zinc-100";
  const numericValue = Number(value);

  if (numericValue > 0) return "text-emerald-300";
  if (numericValue < 0) return "text-rose-300";
  return "text-zinc-100";
}
