"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { getCurrentMonth, isValidMonth } from "@/lib/period";

interface FinanceStoreState {
  referenceMonth: string;
  setReferenceMonth: (month: string) => void;
}

export const useFinanceStore = create<FinanceStoreState>()(
  persist(
    (set) => ({
      referenceMonth: getCurrentMonth(),
      setReferenceMonth: (month: string) => {
        const normalizedMonth = month.trim();

        set({
          referenceMonth: isValidMonth(normalizedMonth) ? normalizedMonth : getCurrentMonth(),
        });
      },
    }),
    {
      name: "finance-store",
      storage: createJSONStorage(() => localStorage),
    }
  )
);