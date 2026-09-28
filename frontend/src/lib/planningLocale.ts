import type { DecimalString, ISODateString } from "@/lib/planning";

export type FinancialInputErrorCode =
  | "EMPTY"
  | "INVALID_CHARACTERS"
  | "INVALID_GROUPING"
  | "TOO_MANY_DECIMALS"
  | "SCIENTIFIC_NOTATION_NOT_ALLOWED"
  | "INVALID_DECIMAL"
  | "INVALID_FORMAT"
  | "INVALID_DATE";

export type FinancialInputResult<T extends string = DecimalString> =
  | { ok: true; value: T }
  | { ok: false; code: FinancialInputErrorCode };

export class FinancialDisplayFormatError extends Error {
  constructor(
    public readonly code: "INVALID_DECIMAL" | "INVALID_DATE" | "INVALID_REFERENCE_MONTH",
  ) {
    super(code);
    this.name = "FinancialDisplayFormatError";
  }
}

type DecimalParts = {
  negative: boolean;
  integer: string;
  fraction: string;
};

const PLAIN_DECIMAL = /^-?\d+(?:\.\d+)?$/;
const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
const BR_DATE = /^(\d{2})\/(\d{2})\/(\d{4})$/;
const REFERENCE_MONTH = /^(\d{4})-(\d{2})$/;

function stripLeadingZeroes(value: string): string {
  const normalized = value.replace(/^0+(?=\d)/, "");
  return normalized === "" ? "0" : normalized;
}

function parsePlainDecimal(value: string): DecimalParts | null {
  if (!PLAIN_DECIMAL.test(value)) {
    return null;
  }

  const negative = value.startsWith("-");
  const unsigned = negative ? value.slice(1) : value;
  const [rawInteger, rawFraction = ""] = unsigned.split(".");
  const integer = stripLeadingZeroes(rawInteger);
  const zero = integer === "0" && /^0*$/.test(rawFraction);

  return {
    negative: negative && !zero,
    integer,
    fraction: rawFraction,
  };
}

function displayError(code: FinancialDisplayFormatError["code"]): never {
  throw new FinancialDisplayFormatError(code);
}

function groupInteger(value: string): string {
  const groups: string[] = [];
  let end = value.length;

  while (end > 3) {
    groups.unshift(value.slice(end - 3, end));
    end -= 3;
  }

  groups.unshift(value.slice(0, end));
  return groups.join(".");
}

function padRight(value: string, length: number): string {
  return value.length >= length ? value : `${value}${"0".repeat(length - value.length)}`;
}

function incrementDigits(value: string): string {
  let carry = 1;
  const output: string[] = [];

  for (let index = value.length - 1; index >= 0; index -= 1) {
    const digit = value.charCodeAt(index) - 48 + carry;
    if (digit === 10) {
      output.unshift("0");
      carry = 1;
    } else {
      output.unshift(String.fromCharCode(48 + digit));
      carry = 0;
    }
  }

  if (carry === 1) {
    output.unshift("1");
  }

  return output.join("");
}

function moveDecimalRight(parts: DecimalParts, places: number): DecimalParts {
  const digits = `${parts.integer}${parts.fraction}`;
  const position = parts.integer.length + places;
  const padded = padRight(digits, position);
  const integer = stripLeadingZeroes(padded.slice(0, position));
  const fraction = padded.slice(position);

  return { negative: parts.negative, integer, fraction };
}

function roundForDisplay(parts: DecimalParts, decimals: number): DecimalParts {
  const keptFraction = padRight(parts.fraction, decimals).slice(0, decimals);
  const nextDigit = parts.fraction.charAt(decimals);
  let combined = `${parts.integer}${keptFraction}`;

  if (nextDigit >= "5") {
    combined = incrementDigits(combined);
  }

  const padded = padRight(combined, decimals + 1);
  const integerEnd = padded.length - decimals;
  const integer = stripLeadingZeroes(padded.slice(0, integerEnd));
  const fraction = decimals === 0 ? "" : padded.slice(integerEnd);
  const zero = integer === "0" && /^0*$/.test(fraction);

  return { negative: parts.negative && !zero, integer, fraction };
}

function formatDecimalParts(parts: DecimalParts, decimals: number): string {
  const decimalPart = decimals === 0 ? "" : `,${padRight(parts.fraction, decimals).slice(0, decimals)}`;
  return `${parts.negative ? "-" : ""}${parts.integer}${decimalPart}`;
}

function digitsToInteger(value: string): number {
  let total = 0;
  for (const character of value) {
    total = total * 10 + character.charCodeAt(0) - 48;
  }
  return total;
}

function isValidCivilDate(year: number, month: number, day: number): boolean {
  const date = new Date(0);
  date.setHours(0, 0, 0, 0);
  date.setFullYear(year, month - 1, day);

  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}

function parseIsoDate(value: string): { year: string; month: string; day: string } | null {
  const match = ISO_DATE.exec(value);
  if (!match) {
    return null;
  }

  const [, year, month, day] = match;
  if (!isValidCivilDate(digitsToInteger(year), digitsToInteger(month), digitsToInteger(day))) {
    return null;
  }

  return { year, month, day };
}

function normalizeFractionFromPercent(integer: string, fraction: string, negative: boolean): DecimalString {
  const sourceDigits = stripLeadingZeroes(`${integer}${fraction}`);
  const scale = fraction.length + 2;
  const wholeLength = sourceDigits.length - scale;
  const resultInteger = wholeLength > 0 ? stripLeadingZeroes(sourceDigits.slice(0, wholeLength)) : "0";
  const resultFraction = (wholeLength > 0
    ? sourceDigits.slice(wholeLength)
    : `${"0".repeat(-wholeLength)}${sourceDigits}`
  ).replace(/0+$/, "");
  const zero = resultInteger === "0" && resultFraction === "";
  const unsigned = resultFraction === "" ? resultInteger : `${resultInteger}.${resultFraction}`;

  return `${negative && !zero ? "-" : ""}${unsigned}`;
}

function parseMoneyInteger(value: string): FinancialInputResult<string> {
  if (value.includes(".")) {
    if (!/^\d{1,3}(?:\.\d{3})+$/.test(value)) {
      return { ok: false, code: "INVALID_GROUPING" };
    }

    return { ok: true, value: value.replaceAll(".", "") };
  }

  if (!/^\d+$/.test(value)) {
    return { ok: false, code: "INVALID_CHARACTERS" };
  }

  return { ok: true, value };
}

function invalidForContext(code: FinancialInputErrorCode, context: "money" | "rate" | "date"): string {
  if (code === "EMPTY") {
    return "Preencha este campo.";
  }

  if (code === "SCIENTIFIC_NOTATION_NOT_ALLOWED") {
    return "Use um número decimal, sem notação científica.";
  }

  if (context === "money") {
    if (code === "INVALID_GROUPING") {
      return "Use o formato 1.000,00.";
    }
    if (code === "TOO_MANY_DECIMALS") {
      return "Use no máximo duas casas decimais.";
    }
    return "Informe um valor monetário válido.";
  }

  if (context === "rate") {
    return "Informe uma taxa como 8% ou 8,5%.";
  }

  if (code === "INVALID_DATE") {
    return "Informe uma data existente.";
  }

  return "Use o formato DD/MM/AAAA.";
}

/** Formats a canonical API money decimal without converting it to a JavaScript number. */
export function formatBRLDecimalString(value: DecimalString): string {
  const parts = parsePlainDecimal(value);
  if (!parts || parts.fraction.length > 2) {
    return displayError("INVALID_DECIMAL");
  }

  return `${parts.negative ? "-" : ""}R$ ${groupInteger(parts.integer)},${padRight(parts.fraction, 2)}`;
}

/** Parses the supported Brazilian money syntax into a canonical two-decimal API string. */
export function parseBRLMoneyInput(raw: string): FinancialInputResult {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return { ok: false, code: "EMPTY" };
  }
  if (/^-?\d+(?:[.,]\d+)?[eE][+-]?\d+$/.test(trimmed)) {
    return { ok: false, code: "SCIENTIFIC_NOTATION_NOT_ALLOWED" };
  }

  let value = trimmed.replace(/^R\$\s*/i, "").trim();
  let negative = false;
  if (value.startsWith("-")) {
    negative = true;
    value = value.slice(1);
  }
  if (value === "" || value.includes("-") || !/^[\d.,]+$/.test(value)) {
    return { ok: false, code: "INVALID_CHARACTERS" };
  }

  const decimalParts = value.split(",");
  if (decimalParts.length > 2) {
    return { ok: false, code: "INVALID_DECIMAL" };
  }

  const [rawInteger, rawFraction] = decimalParts;
  const parsedInteger = parseMoneyInteger(rawInteger);
  if (!parsedInteger.ok) {
    return parsedInteger;
  }
  if (rawFraction !== undefined && !/^\d+$/.test(rawFraction)) {
    return { ok: false, code: "INVALID_DECIMAL" };
  }
  if (rawFraction !== undefined && rawFraction.length > 2) {
    return { ok: false, code: "TOO_MANY_DECIMALS" };
  }

  const integer = stripLeadingZeroes(parsedInteger.value);
  const fraction = rawFraction === undefined ? "00" : padRight(rawFraction, 2);
  const zero = integer === "0" && /^0*$/.test(fraction);
  return { ok: true, value: `${negative && !zero ? "-" : ""}${integer}.${fraction}` };
}

/** Formats a canonical fraction as a human percentage with deterministic string-only rounding. */
export function formatRateDecimalString(
  fraction: DecimalString,
  decimals: number,
  suffix: string,
): string {
  if (decimals < 0 || decimals % 1 !== 0) {
    throw new RangeError("Rate display decimals must be a non-negative integer.");
  }

  const parts = parsePlainDecimal(fraction);
  if (!parts) {
    return displayError("INVALID_DECIMAL");
  }

  const percentage = moveDecimalRight(parts, 2);
  return `${formatDecimalParts(roundForDisplay(percentage, decimals), decimals)}%${suffix}`;
}

export function formatAnnualRateDecimalString(fraction: DecimalString): string {
  return formatRateDecimalString(fraction, 2, " a.a.");
}

export function formatMonthlyRateDecimalString(fraction: DecimalString): string {
  return formatRateDecimalString(fraction, 4, " a.m.");
}

/** Parses a human percentage into the fraction required by the Planning API. */
export function parseBRPercentInputToFraction(raw: string): FinancialInputResult {
  let value = raw.trim();
  if (value === "") {
    return { ok: false, code: "EMPTY" };
  }
  if (/^-?\d+(?:[.,]\d+)?[eE][+-]?\d+$/.test(value)) {
    return { ok: false, code: "SCIENTIFIC_NOTATION_NOT_ALLOWED" };
  }

  if (value.endsWith("%")) {
    value = value.slice(0, -1).trim();
  }
  if (value === "" || value.includes("%")) {
    return { ok: false, code: "INVALID_CHARACTERS" };
  }

  let negative = false;
  if (value.startsWith("-")) {
    negative = true;
    value = value.slice(1);
  }
  if (value === "" || value.includes("-") || !/^\d+(?:[,.]\d+)?$/.test(value)) {
    return { ok: false, code: "INVALID_DECIMAL" };
  }

  const [integer, fraction = ""] = value.replace(",", ".").split(".");
  return { ok: true, value: normalizeFractionFromPercent(integer, fraction, negative) };
}

export function formatBRDate(value: ISODateString): string {
  const date = parseIsoDate(value);
  if (!date) {
    return displayError("INVALID_DATE");
  }

  return `${date.day}/${date.month}/${date.year}`;
}

export function parseBRDateInput(raw: string): FinancialInputResult<ISODateString> {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return { ok: false, code: "EMPTY" };
  }

  const match = BR_DATE.exec(trimmed);
  if (!match) {
    return { ok: false, code: "INVALID_FORMAT" };
  }

  const [, day, month, year] = match;
  if (!isValidCivilDate(digitsToInteger(year), digitsToInteger(month), digitsToInteger(day))) {
    return { ok: false, code: "INVALID_DATE" };
  }

  return { ok: true, value: `${year}-${month}-${day}` };
}

/** Returns a local civil date and intentionally never serializes through UTC ISO. */
export function formatLocalISODate(date: Date): ISODateString {
  if (!(date instanceof Date) || date.toString() === "Invalid Date") {
    return displayError("INVALID_DATE");
  }

  const year = String(date.getFullYear()).padStart(4, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Formats a monthly reference bucket without inventing a daily valuation date. */
export function formatReferenceMonth(value: string): string {
  const match = REFERENCE_MONTH.exec(value);
  if (!match) {
    return displayError("INVALID_REFERENCE_MONTH");
  }

  const [, year, month] = match;
  const numericMonth = digitsToInteger(month);
  if (numericMonth < 1 || numericMonth > 12) {
    return displayError("INVALID_REFERENCE_MONTH");
  }

  return `${month}/${year}`;
}

/** Keeps parser error codes separate from Portuguese field-level copy. */
export function formatFinancialInputError(
  code: FinancialInputErrorCode,
  context: "money" | "rate" | "date",
): string {
  return invalidForContext(code, context);
}
