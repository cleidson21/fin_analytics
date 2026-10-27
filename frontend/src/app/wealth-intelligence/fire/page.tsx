"use client";

import { useState } from "react";

import { PageLayout } from "@/components/layout/PageLayout";
import { analyzeFire, type FireAnalysisType } from "@/lib/fire";

import { ShowOnWealthHomeButton } from "../components/ShowOnWealthHomeButton";
import { FireInputs } from "./components/FireInputs";
import { buildFireRequest, createFireForm, FireInputError, normalizeFireMode } from "./components/fireForm";
import {
  beginFireSubmission,
  completeFireSubmission,
  createFireResultState,
  failFireSubmission,
  FireResultRegion,
} from "./components/FireResults";

export default function FirePage() {
  const [form, setForm] = useState(createFireForm);
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [resultState, setResultState] = useState(createFireResultState);
  const currentSnapshot = JSON.stringify(form);
  const submitLabel = form.mode === "SUMMARY"
    ? "Analisar independência"
    : form.mode === "PROJECTED_DATE"
      ? "Projetar data"
      : "Calcular aporte";

  const patch = (value: Partial<typeof form>) => setForm((current) => ({ ...current, ...value }));
  const changeMode = (mode: FireAnalysisType) => {
    setForm((current) => normalizeFireMode(current, mode));
    setErrors({});
  };

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setErrors({});

    let request;
    try {
      request = buildFireRequest(form, new Date());
    } catch (error) {
      if (error instanceof FireInputError) setErrors({ [error.field]: error.message });
      return;
    }

    const submittedSnapshot = currentSnapshot;
    setResultState((current) => beginFireSubmission(current));
    try {
      const response = await analyzeFire(request);
      if (!response) throw new Error("Não foi possível concluir a análise agora.");
      setResultState((current) => completeFireSubmission(current, response, submittedSnapshot));
    } catch (error) {
      setResultState((current) => failFireSubmission(
        current,
        error instanceof Error ? error.message : "Não foi possível concluir a análise agora.",
      ));
    }
  }

  return (
    <PageLayout title="Independência Financeira" subtitle="" hideTitle>
      <main className="mx-auto w-full max-w-5xl py-2">
        <h1 className="sr-only">Independência Financeira</h1>
        <form onSubmit={submit} className="rounded-2xl border border-border bg-muted/30 p-4 sm:p-5">
          <FireInputs value={form} errors={errors} onChange={patch} onMode={changeMode} />
          <div className="mt-5 flex justify-end border-t border-border pt-4">
            <button
              type="submit"
              disabled={resultState.pending}
              className="w-full rounded-xl bg-violet-300 px-5 py-2.5 text-sm font-semibold text-zinc-950 transition-colors hover:bg-violet-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-300 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {resultState.pending ? "Calculando…" : submitLabel}
            </button>
          </div>
        </form>
        <FireResultRegion
          state={resultState}
          currentSnapshot={currentSnapshot}
          action={resultState.result ? (
            <ShowOnWealthHomeButton
              analysis={{ domain: "FIRE", kind: "FIRE_ANALYSIS", result: resultState.result }}
            />
          ) : null}
        />
      </main>
    </PageLayout>
  );
}
