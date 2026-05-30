const MONTH_PATTERN = /^\d{4}-\d{2}$/;

export function getCurrentMonth() {
  return new Date().toISOString().slice(0, 7);
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