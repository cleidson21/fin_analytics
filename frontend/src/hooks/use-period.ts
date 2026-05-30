"use client";

import { useFinanceStore } from "@/store/finance-store";
import { getCurrentMonth } from "@/lib/period";

export function usePeriod() {
  const month = useFinanceStore((state) => state.referenceMonth);
  const setMonth = useFinanceStore((state) => state.setReferenceMonth);

  return {
    month,
    setMonth,
    fallbackMonth: getCurrentMonth(),
  };
}