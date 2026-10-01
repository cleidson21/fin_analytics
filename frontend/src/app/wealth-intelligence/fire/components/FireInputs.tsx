"use client";

import { cloneElement, type InputHTMLAttributes, type ReactElement } from "react";

import type { FireAnalysisType } from "@/lib/fire";
import type { FireFormState } from "./fireForm";

type Props = { value: FireFormState; errors: Partial<Record<string, string>>; onChange: (patch: Partial<FireFormState>) => void; onMode: (mode: FireAnalysisType) => void };
const modes: { value: FireAnalysisType; label: string; question: string }[] = [
  { value: "SUMMARY", label: "Resumo", question: "Quanto preciso e quanto já avancei?" },
  { value: "PROJECTED_DATE", label: "Quando atinjo?", question: "Em quanto tempo posso alcançar minha meta?" },
  { value: "REQUIRED_CONTRIBUTION", label: "Quanto preciso aportar?", question: "Qual aporte mensal pode me levar até lá?" },
];
const inputClassName = "rounded-lg border border-white/10 bg-zinc-950 px-3 py-2";

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactElement<InputHTMLAttributes<HTMLInputElement>> }) {
  const errorId = error ? id + "-error" : undefined;
  return <label className="grid gap-1.5 text-sm font-medium text-zinc-200"><span>{label}</span>{cloneElement(children, { "aria-describedby": errorId })}{error ? <span id={errorId} role="alert" className="text-xs text-rose-300">{error}</span> : null}</label>;
}

export function FireInputs({ value, errors, onChange, onMode }: Props) {
  const needsProjection = value.mode !== "SUMMARY";
  return <div className="grid gap-6">
    <fieldset className="grid gap-3">
      <legend className="text-sm font-semibold text-zinc-100">O que você quer explorar?</legend>
      <div className="grid gap-2 sm:grid-cols-3">{modes.map((mode) => <button key={mode.value} type="button" aria-pressed={value.mode === mode.value} onClick={() => onMode(mode.value)} className={["rounded-xl border p-3 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-300", value.mode === mode.value ? "border-violet-300/50 bg-violet-300/10 text-white" : "border-white/10 text-zinc-400"].join(" ")}><span className="block text-sm font-semibold">{mode.label}</span><span className="mt-1 block text-xs leading-5">{mode.question}</span></button>)}</div>
    </fieldset>
    <fieldset className="grid gap-4">
      <legend className="text-sm font-semibold text-zinc-100">Ponto de partida</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        <button type="button" aria-pressed={value.source === "INVESTMENT_PORTFOLIO_SNAPSHOT"} onClick={() => onChange({ source: "INVESTMENT_PORTFOLIO_SNAPSHOT" })} className={["rounded-xl border p-3 text-left", value.source === "INVESTMENT_PORTFOLIO_SNAPSHOT" ? "border-emerald-300/50 bg-emerald-300/10" : "border-white/10"].join(" ")}>Carteira de investimentos<span className="mt-1 block text-xs text-zinc-400">Usa a carteira disponível no sistema; não é o patrimônio líquido total.</span></button>
        <button type="button" aria-pressed={value.source === "USER_PROVIDED_SCENARIO"} onClick={() => onChange({ source: "USER_PROVIDED_SCENARIO" })} className={["rounded-xl border p-3 text-left", value.source === "USER_PROVIDED_SCENARIO" ? "border-emerald-300/50 bg-emerald-300/10" : "border-white/10"].join(" ")}>Valor informado por mim</button>
      </div>
      {value.source === "USER_PROVIDED_SCENARIO" ? <Field id="fire-wealth" label="Valor patrimonial" error={errors.wealth}><input value={value.wealth} onChange={(event) => onChange({ wealth: event.target.value })} placeholder="R$ 250.000,00" className={inputClassName} /></Field> : null}
    </fieldset>
    <div className="grid gap-4 sm:grid-cols-2">
      <Field id="fire-spending" label="Gasto mensal desejado na independência" error={errors.spending}><input value={value.spending} onChange={(event) => onChange({ spending: event.target.value })} placeholder="R$ 5.000,00" className={inputClassName} /></Field>
      <Field id="fire-withdrawal-rate" label="Taxa anual de retirada assumida" error={errors.withdrawalRate}><input value={value.withdrawalRate} onChange={(event) => onChange({ withdrawalRate: event.target.value })} placeholder="4" className={inputClassName} /></Field>
    </div>
    {needsProjection ? <>
      <div className="grid gap-4 sm:grid-cols-2">
        {value.mode === "PROJECTED_DATE" ? <><Field id="fire-contribution" label="Aporte mensal do cenário" error={errors.contribution}><input value={value.contribution} onChange={(event) => onChange({ contribution: event.target.value })} placeholder="R$ 1.000,00" className={inputClassName} /></Field><Field id="fire-horizon" label="Horizonte (meses)" error={errors.horizon}><input inputMode="numeric" value={value.horizon} onChange={(event) => onChange({ horizon: event.target.value })} placeholder="120" className={inputClassName} /></Field></> : null}
        {value.mode === "REQUIRED_CONTRIBUTION" ? <Field id="fire-desired-date" label="Data desejada para independência" error={errors.desiredDate}><input value={value.desiredDate} onChange={(event) => onChange({ desiredDate: event.target.value })} placeholder="30/09/2036" className={inputClassName} /></Field> : null}
        <Field id="fire-expected-return" label="Retorno anual esperado" error={errors.expectedReturn}><input value={value.expectedReturn} onChange={(event) => onChange({ expectedReturn: event.target.value })} placeholder="5" className={inputClassName} /></Field>
      </div>
      <details className="rounded-xl border border-white/10 p-4"><summary className="cursor-pointer text-sm font-medium text-zinc-200">Premissas avançadas</summary><label className="mt-3 flex items-center gap-2 text-sm"><input type="checkbox" checked={value.returnType === "NOMINAL"} onChange={(event) => onChange({ returnType: event.target.checked ? "NOMINAL" : "REAL", inflation: event.target.checked ? value.inflation : "" })} /> Minha premissa de retorno é nominal</label>{value.returnType === "NOMINAL" ? <div className="mt-3"><Field id="fire-inflation" label="Inflação anual esperada" error={errors.inflation}><input value={value.inflation} onChange={(event) => onChange({ inflation: event.target.value })} placeholder="4" className={inputClassName} /></Field></div> : null}</details>
    </> : null}
  </div>;
}
