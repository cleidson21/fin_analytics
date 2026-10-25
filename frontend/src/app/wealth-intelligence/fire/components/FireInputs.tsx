"use client";

import { cloneElement, type InputHTMLAttributes, type ReactElement } from "react";
import { CalendarClock, CircleDollarSign, Gauge } from "lucide-react";

import type { FireAnalysisType } from "@/lib/fire";
import type { FireFormState } from "./fireForm";

type Props = {
  value: FireFormState;
  errors: Partial<Record<string, string>>;
  onChange: (patch: Partial<FireFormState>) => void;
  onMode: (mode: FireAnalysisType) => void;
};

const modes = [
  {
    value: "SUMMARY" as const,
    label: "Diagnóstico atual",
    icon: Gauge,
  },
  {
    value: "PROJECTED_DATE" as const,
    label: "Previsão de alcance",
    icon: CalendarClock,
  },
  {
    value: "REQUIRED_CONTRIBUTION" as const,
    label: "Aporte necessário",
    icon: CircleDollarSign,
  },
];

const inputClassName = "min-h-10 rounded-lg border border-border bg-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-violet-300/40 focus:outline-none focus:ring-2 focus:ring-violet-300/15";

function Field({ id, label, error, children }: {
  id: string;
  label: string;
  error?: string;
  children: ReactElement<InputHTMLAttributes<HTMLInputElement>>;
}) {
  const errorId = error ? `${id}-error` : undefined;
  return (
    <label className="grid gap-1.5 text-sm font-medium text-foreground">
      <span>{label}</span>
      {cloneElement(children, { id, "aria-describedby": errorId })}
      {error ? <span id={errorId} role="alert" className="text-xs text-destructive">{error}</span> : null}
    </label>
  );
}

export function FireInputs({ value, errors, onChange, onMode }: Props) {
  const needsProjection = value.mode !== "SUMMARY";

  return (
    <div className="grid gap-5">
      <fieldset className="grid gap-3">
        <legend className="text-sm font-semibold text-foreground">1. Escolha a análise</legend>
        <div className="flex gap-1 overflow-x-auto rounded-xl border border-border bg-background p-1">
          {modes.map((mode) => {
            const Icon = mode.icon;
            const selected = value.mode === mode.value;
            return (
              <button
                key={mode.value}
                type="button"
                aria-pressed={selected}
                onClick={() => onMode(mode.value)}
                className={`min-h-11 min-w-44 flex-1 rounded-lg border px-3 py-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/50 ${selected ? "border-violet-300/40 bg-violet-300/12 text-foreground" : "border-transparent text-muted-foreground hover:border-border hover:bg-muted/40"}`}
              >
                <span className="flex items-center gap-2 text-sm font-semibold">
                  <Icon aria-hidden="true" className={`size-4 ${selected ? "text-violet-700 dark:text-violet-300" : "text-muted-foreground"}`} />
                  {mode.label}
                </span>
              </button>
            );
          })}
        </div>
      </fieldset>

      <fieldset className="grid gap-3 border-t border-border pt-4">
        <legend className="px-1 text-sm font-semibold text-foreground">2. Defina o ponto de partida</legend>
        <div className="grid gap-2 sm:grid-cols-2">
          <button
            type="button"
            aria-pressed={value.source === "INVESTMENT_PORTFOLIO_SNAPSHOT"}
            onClick={() => onChange({ source: "INVESTMENT_PORTFOLIO_SNAPSHOT" })}
            className={`rounded-xl border p-3 text-left text-sm font-medium transition ${value.source === "INVESTMENT_PORTFOLIO_SNAPSHOT" ? "border-emerald-300/50 bg-emerald-300/10 text-success-foreground" : "border-border text-foreground/90 hover:bg-muted/40"}`}
          >
            Carteira de investimentos
            <span className="mt-1 block text-xs font-normal leading-5 text-muted-foreground">Patrimônio elegível disponível no sistema.</span>
          </button>
          <button
            type="button"
            aria-pressed={value.source === "USER_PROVIDED_SCENARIO"}
            onClick={() => onChange({ source: "USER_PROVIDED_SCENARIO" })}
            className={`rounded-xl border p-3 text-left text-sm font-medium transition ${value.source === "USER_PROVIDED_SCENARIO" ? "border-emerald-300/50 bg-emerald-300/10 text-success-foreground" : "border-border text-foreground/90 hover:bg-muted/40"}`}
          >
            Valor informado por mim
            <span className="mt-1 block text-xs font-normal leading-5 text-muted-foreground">Cenário transitório; não altera sua carteira.</span>
          </button>
        </div>
        {value.source === "USER_PROVIDED_SCENARIO" ? (
          <Field id="fire-wealth" label="Patrimônio inicial (BRL)" error={errors.wealth}>
            <input value={value.wealth} onChange={(event) => onChange({ wealth: event.target.value })} placeholder="R$ 250.000,00" className={inputClassName} />
          </Field>
        ) : null}
      </fieldset>

      <fieldset className="grid gap-4 border-t border-border pt-4">
        <legend className="px-1 text-sm font-semibold text-foreground">3. Informe as premissas</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="fire-spending" label="Gasto mensal desejado (BRL)" error={errors.spending}>
            <input value={value.spending} onChange={(event) => onChange({ spending: event.target.value })} placeholder="R$ 5.000,00" className={inputClassName} />
          </Field>
          <Field id="fire-withdrawal-rate" label="Taxa anual de retirada (% a.a.)" error={errors.withdrawalRate}>
            <input value={value.withdrawalRate} onChange={(event) => onChange({ withdrawalRate: event.target.value })} placeholder="4" className={inputClassName} />
          </Field>
          {value.mode === "PROJECTED_DATE" ? (
            <>
              <Field id="fire-contribution" label="Aporte mensal do cenário (BRL)" error={errors.contribution}>
                <input value={value.contribution} onChange={(event) => onChange({ contribution: event.target.value })} placeholder="R$ 1.000,00" className={inputClassName} />
              </Field>
              <Field id="fire-horizon" label="Horizonte (meses)" error={errors.horizon}>
                <input inputMode="numeric" value={value.horizon} onChange={(event) => onChange({ horizon: event.target.value })} placeholder="120" className={inputClassName} />
              </Field>
            </>
          ) : null}
          {value.mode === "REQUIRED_CONTRIBUTION" ? (
            <Field id="fire-desired-date" label="Data desejada para independência" error={errors.desiredDate}>
              <input value={value.desiredDate} onChange={(event) => onChange({ desiredDate: event.target.value })} placeholder="30/09/2036" className={inputClassName} />
            </Field>
          ) : null}
          {needsProjection ? (
            <Field id="fire-expected-return" label="Retorno anual esperado (% a.a.)" error={errors.expectedReturn}>
              <input value={value.expectedReturn} onChange={(event) => onChange({ expectedReturn: event.target.value })} placeholder="5" className={inputClassName} />
            </Field>
          ) : null}
        </div>

        {needsProjection ? (
          <details className="rounded-xl border border-border bg-muted/25 p-4">
            <summary className="cursor-pointer text-sm font-medium text-foreground">Premissas avançadas</summary>
            <label className="mt-3 flex items-center gap-2 text-sm text-foreground/90">
              <input
                type="checkbox"
                checked={value.returnType === "NOMINAL"}
                onChange={(event) => onChange({ returnType: event.target.checked ? "NOMINAL" : "REAL", inflation: event.target.checked ? value.inflation : "" })}
              />
              Minha premissa de retorno é nominal
            </label>
            {value.returnType === "NOMINAL" ? (
              <div className="mt-3 max-w-sm">
                <Field id="fire-inflation" label="Inflação anual esperada (% a.a.)" error={errors.inflation}>
                  <input value={value.inflation} onChange={(event) => onChange({ inflation: event.target.value })} placeholder="4" className={inputClassName} />
                </Field>
              </div>
            ) : null}
          </details>
        ) : null}
      </fieldset>
    </div>
  );
}
