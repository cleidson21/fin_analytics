import { describe, expect, it } from "vitest";

import {
  FinancialDisplayFormatError,
  formatAnnualRateDecimalString,
  formatBRDate,
  formatBRLDecimalString,
  formatFinancialInputError,
  formatLocalISODate,
  formatMonthlyRateDecimalString,
  formatReferenceMonth,
  parseBRDateInput,
  parseBRLMoneyInput,
  parseBRPercentInputToFraction,
} from "./planningLocale";

describe("formatBRLDecimalString", () => {
  it.each([
    ["0", "R$ 0,00"],
    ["1", "R$ 1,00"],
    ["200", "R$ 200,00"],
    ["1000", "R$ 1.000,00"],
    ["1000.5", "R$ 1.000,50"],
    ["1000.50", "R$ 1.000,50"],
    ["112594.46", "R$ 112.594,46"],
    ["-1454.18", "-R$ 1.454,18"],
    ["12345678901234567890.12", "R$ 12.345.678.901.234.567.890,12"],
  ])("formats %s as %s", (value, expected) => {
    expect(formatBRLDecimalString(value)).toBe(expected);
  });

  it("rejects non-canonical money instead of fabricating a value", () => {
    expect(() => formatBRLDecimalString("1e3")).toThrow(FinancialDisplayFormatError);
    expect(() => formatBRLDecimalString("1.234")).toThrow(FinancialDisplayFormatError);
  });
});

describe("parseBRLMoneyInput", () => {
  it.each([
    ["1000", "1000.00"],
    ["1.000", "1000.00"],
    ["1.000,50", "1000.50"],
    ["R$ 1.000,50", "1000.50"],
    ["  R$ 1.000,50  ", "1000.50"],
    ["-1.000,50", "-1000.50"],
  ])("parses %s", (raw, expected) => {
    expect(parseBRLMoneyInput(raw)).toEqual({ ok: true, value: expected });
  });

  it.each([
    ["1000.50", "INVALID_GROUPING"],
    ["1,234", "TOO_MANY_DECIMALS"],
    ["1e3", "SCIENTIFIC_NOTATION_NOT_ALLOWED"],
    ["1.00,50", "INVALID_GROUPING"],
    ["1.000.00", "INVALID_GROUPING"],
    ["10.00", "INVALID_GROUPING"],
    ["1.00.000", "INVALID_GROUPING"],
    ["1000.000", "INVALID_GROUPING"],
    ["1.0000", "INVALID_GROUPING"],
    ["R$ abc", "INVALID_CHARACTERS"],
    ["", "EMPTY"],
  ])("rejects %s", (raw, code) => {
    expect(parseBRLMoneyInput(raw)).toEqual({ ok: false, code });
  });
});

describe("rate display", () => {
  it.each([
    ["0", "0,00% a.a."],
    ["0.08", "8,00% a.a."],
    ["0.085", "8,50% a.a."],
    ["-0.01", "-1,00% a.a."],
    ["0.012345", "1,23% a.a."],
    ["0.012355", "1,24% a.a."],
  ])("formats annual rate %s", (fraction, expected) => {
    expect(formatAnnualRateDecimalString(fraction)).toBe(expected);
  });

  it("formats long monthly rates without exposing technical precision", () => {
    expect(formatMonthlyRateDecimalString("0.006434030110003")).toBe("0,6434% a.m.");
  });
});

describe("parseBRPercentInputToFraction", () => {
  it.each([
    ["8", "0.08"],
    ["8%", "0.08"],
    ["8,5", "0.085"],
    ["8,5%", "0.085"],
    ["0,08", "0.0008"],
    ["0,08%", "0.0008"],
    ["8.5", "0.085"],
    ["-1%", "-0.01"],
  ])("parses %s as a fraction", (raw, expected) => {
    expect(parseBRPercentInputToFraction(raw)).toEqual({ ok: true, value: expected });
  });

  it.each([
    ["1e2", "SCIENTIFIC_NOTATION_NOT_ALLOWED"],
    ["%%", "INVALID_CHARACTERS"],
    ["8,,5", "INVALID_DECIMAL"],
    ["texto", "INVALID_DECIMAL"],
  ])("rejects %s", (raw, code) => {
    expect(parseBRPercentInputToFraction(raw)).toEqual({ ok: false, code });
  });
});

describe("civil date primitives", () => {
  it.each([
    ["2026-09-26", "26/09/2026"],
    ["2028-02-29", "29/02/2028"],
  ])("formats ISO dates", (value, expected) => {
    expect(formatBRDate(value)).toBe(expected);
  });

  it.each([
    ["26/09/2026", { ok: true, value: "2026-09-26" }],
    ["29/02/2028", { ok: true, value: "2028-02-29" }],
    ["31/02/2026", { ok: false, code: "INVALID_DATE" }],
    ["29/02/2027", { ok: false, code: "INVALID_DATE" }],
    ["31/13/2026", { ok: false, code: "INVALID_DATE" }],
    ["2026-09-26", { ok: false, code: "INVALID_FORMAT" }],
  ])("parses Brazilian dates", (raw, expected) => {
    expect(parseBRDateInput(raw)).toEqual(expected);
  });

  it("formats a local civil date without serializing through UTC", () => {
    const localDate = new Date(0);
    localDate.setFullYear(2026, 8, 26);
    localDate.setHours(23, 30, 0, 0);

    expect(formatLocalISODate(localDate)).toBe("2026-09-26");
  });

  it("formats reference months without fabricating a day", () => {
    expect(formatReferenceMonth("2026-09")).toBe("09/2026");
    expect(() => formatReferenceMonth("2026-13")).toThrow(FinancialDisplayFormatError);
  });
});

describe("structured error copy", () => {
  it("maps lexical errors separately from parsers", () => {
    expect(formatFinancialInputError("INVALID_GROUPING", "money")).toBe("Use o formato 1.000,00.");
    expect(formatFinancialInputError("INVALID_DECIMAL", "rate")).toBe("Informe uma taxa como 8% ou 8,5%.");
    expect(formatFinancialInputError("INVALID_DATE", "date")).toBe("Informe uma data existente.");
  });
});
