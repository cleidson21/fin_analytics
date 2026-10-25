"use client";

import { useRouter } from "next/navigation";
import { ArrowUpRight } from "lucide-react";

import { useTransientAnalysis } from "../TransientAnalysisContext";
import { isSelectableAnalysis, type TransientAnalysisCandidate } from "../transientAnalysis";

export function ShowOnWealthHomeButton({
  analysis,
}: {
  analysis: TransientAnalysisCandidate;
}) {
  const router = useRouter();
  const { selectAnalysis } = useTransientAnalysis();

  if (!isSelectableAnalysis(analysis)) return null;

  function showOnHome() {
    if (!selectAnalysis(analysis)) return;
    router.push("/wealth-intelligence");
  }

  return (
    <button
      type="button"
      onClick={showOnHome}
      className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-emerald-300/25 bg-emerald-300/10 px-4 text-sm font-semibold text-success-foreground transition hover:bg-emerald-300/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/50"
    >
      Mostrar na Visão Geral
      <ArrowUpRight aria-hidden="true" size={16} />
    </button>
  );
}
