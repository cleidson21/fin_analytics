"use client";

if (typeof window !== "undefined") {
  const originalConsoleWarn = console.warn;
  const originalConsoleError = console.error;

  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      args[0].includes("The width(-1) and height(-1) of chart should be greater than 0")
    ) {
      return;
    }
    originalConsoleWarn(...args);
  };

  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      args[0].includes("The width(-1) and height(-1) of chart should be greater than 0")
    ) {
      return;
    }
    originalConsoleError(...args);
  };
}

export function RechartsConsoleWarningFix() {
  return null;
}
