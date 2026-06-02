const MONTH_PATTERN = /^\d{4}-\d{2}$/;

export function getCurrentMonth() {
  return new Date().toISOString().slice(0, 7);
}

export function getMonthBounds(month: string) {
  const [year, monthNumber] = month.split("-").map(Number);
  const startDate = `${month}-01`;
  const endDate = new Date(Date.UTC(year, monthNumber, 0)).toISOString().slice(0, 10);

  return {
    startDate,
    endDate,
  };
}

export function addMonths(month: string, delta: number): string {
  const [year, m] = month.split("-").map(Number);
  const date = new Date(year, m - 1 + delta, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

export function formatMonthLabel(month: string): string {
  const [year, m] = month.split("-").map(Number);
  const MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
  ];
  return `${MONTHS[m - 1]} de ${year}`;
}

export function resolveMonth(value: string | string[] | undefined | null) {
  const candidate = Array.isArray(value) ? value[0] : value;
  const month = candidate?.trim();

  if (month && MONTH_PATTERN.test(month)) {
    return month;
  }

  return getCurrentMonth();
}

export function isValidMonth(value: string) {
  return MONTH_PATTERN.test(value);
}