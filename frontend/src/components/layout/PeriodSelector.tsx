"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { CalendarRange } from "lucide-react";

import { usePeriod } from "@/hooks/use-period";
import { isValidMonth } from "@/lib/period";

export function PeriodSelector() {
  const searchParams = useSearchParams();
  const { month, setMonth } = usePeriod();

  useEffect(() => {
    const urlMonth = searchParams.get("month");

    if (urlMonth && isValidMonth(urlMonth) && urlMonth !== month) {
      setMonth(urlMonth);
    }
  }, [month, searchParams, setMonth]);

  return (
    <label className="inline-flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300 shadow-lg shadow-black/10 backdrop-blur transition-colors hover:bg-white/10">
      <span className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
        <CalendarRange className="size-4 text-emerald-300" />
        Período
      </span>
      <input
        type="month"
        value={month}
        onChange={(event) => setMonth(event.target.value)}
        className="min-w-[9rem] bg-transparent text-sm text-zinc-100 outline-none"
        aria-label="Selecionar período"
      />
    </label>
  );
}