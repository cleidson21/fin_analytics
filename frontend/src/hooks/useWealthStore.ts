import { create } from "zustand";
import { WealthPeriod } from "@/components/wealth/ui/WealthPeriodToggle";

interface WealthState {
  period: WealthPeriod;
  setPeriod: (period: WealthPeriod) => void;
}

export const useWealthStore = create<WealthState>((set) => ({
  period: "1A",
  setPeriod: (period) => set({ period }),
}));
