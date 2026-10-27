"use client";

import { useId, useState, type ReactNode } from "react";
import { ChevronDown, Info } from "lucide-react";

import {
  GOAL_STATUS_LABELS,
  GOAL_TYPE_LABELS,
  type Goal,
} from "@/app/goals/types";
import type { OutputMode, ReturnType } from "@/lib/planning";

import { type PlanningInputField, type PlanningInputState } from "./planningForm";

type PlanningInputsProps = {
  value: PlanningInputState;
  onChange: (value: PlanningInputState) => void;
  goals: Goal[];
  idPrefix: string;
  goalSourceMode?: "selector" | "path";
  fieldErrors?: Partial<Record<PlanningInputField, string>>;
  onFieldChange?: (field: PlanningInputField) => void;
  advancedSlot?: ReactNode;
  comparisonScenario?: boolean;
  comparisonOutputMode?: OutputMode;
  onReturnTypeChange?: (returnType: ReturnType) => void;
};

const inputClassName = "min-h-10 w-full rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-400/10";

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? <span id={id} className="text-xs font-normal text-destructive">{message}</span> : null;
}

export function PlanningInputs({
  value,
  onChange,
  goals,
  idPrefix,
  goalSourceMode = "selector",
  fieldErrors = {},
  onFieldChange,
  advancedSlot,
  comparisonScenario = false,
  comparisonOutputMode,
  onReturnTypeChange,
}: PlanningInputsProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [portfolioInfoOpen, setPortfolioInfoOpen] = useState(false);
  const advancedId = useId();
  const portfolioInfoId = useId();
  const effectiveOutputMode = comparisonScenario ? comparisonOutputMode ?? value.outputMode : value.outputMode;
  const showInflation = value.returnType === "NOMINAL" && effectiveOutputMode === "REAL";
  const hasNonDefaultConfiguration =
    value.returnType !== "NOMINAL" ||
    (!comparisonScenario && value.outputMode !== "NOMINAL") ||
    (!comparisonScenario && value.asOfDate !== "") ||
    value.observedAt !== "";
  const basisSummary = effectiveOutputMode === "REAL"
    ? "Valores reais"
    : value.returnType === "REAL"
      ? "Retorno real"
      : "Valores nominais";

  function patch(next: Partial<PlanningInputState>, field?: PlanningInputField) {
    onChange({ ...value, ...next });
    if (field) onFieldChange?.(field);
  }

  function updateReturnType(returnType: ReturnType) {
    const outputMode = comparisonScenario
      ? effectiveOutputMode
      : returnType === "REAL" && value.outputMode === "NOMINAL" ? "REAL" : value.outputMode;
    const nextRequiresInflation = returnType === "NOMINAL" && outputMode === "REAL";

    patch({
      returnType,
      outputMode,
      inflationRate: nextRequiresInflation ? value.inflationRate : "",
    }, "expectedReturnRate");
    onReturnTypeChange?.(returnType);
  }

  function updateOutputMode(outputMode: OutputMode) {
    const nextOutputMode = value.returnType === "REAL" && outputMode === "NOMINAL" ? "REAL" : outputMode;
    const nextRequiresInflation = value.returnType === "NOMINAL" && nextOutputMode === "REAL";

    patch({
      outputMode: nextOutputMode,
      inflationRate: nextRequiresInflation ? value.inflationRate : "",
    }, "inflationRate");
  }

  return (
    <fieldset className="space-y-3">
      <div className={comparisonScenario ? "grid gap-3 sm:grid-cols-2" : "grid gap-3 sm:grid-cols-2 xl:grid-cols-3"}>
        <label className={`flex min-w-0 flex-col gap-1.5 text-sm font-medium text-foreground/90 ${comparisonScenario ? "sm:col-span-2" : ""}`}>
          Origem do patrimônio inicial
          <select
            id={`${idPrefix}-source`}
            value={value.source}
            onChange={(event) => patch({ source: event.target.value as PlanningInputState["source"] })}
            className={`${inputClassName} min-w-0`}
          >
            <option value="USER_PROVIDED_SCENARIO">Informar patrimônio inicial</option>
            <option value="GOAL_CURRENT_AMOUNT">Valor atual da meta</option>
            <option value="INVESTMENT_PORTFOLIO_SNAPSHOT">Carteira de investimentos MyProfit</option>
          </select>
        </label>

        {value.source === "USER_PROVIDED_SCENARIO" ? (
          <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
            Patrimônio inicial
            <input
              required
              value={value.initialWealth}
              onChange={(event) => patch({ initialWealth: event.target.value }, "initialWealth")}
              placeholder="Ex.: R$ 1.000,00"
              inputMode="decimal"
              aria-describedby={fieldErrors.initialWealth ? `${idPrefix}-initial-wealth-error` : undefined}
              className={inputClassName}
            />
            <FieldError id={`${idPrefix}-initial-wealth-error`} message={fieldErrors.initialWealth} />
          </label>
        ) : value.source === "INVESTMENT_PORTFOLIO_SNAPSHOT" ? (
          <div className="self-end text-sm text-muted-foreground sm:col-span-2 xl:col-span-2">
            <div className="flex items-center gap-1.5">
              <span>Carteira de investimentos MyProfit</span>
              <button
                type="button"
                aria-expanded={portfolioInfoOpen}
                aria-controls={portfolioInfoId}
                onClick={() => setPortfolioInfoOpen((current) => !current)}
                className="rounded-full p-1 text-muted-foreground transition hover:bg-muted/55 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/50"
              >
                <Info aria-hidden="true" size={16} />
                <span className="sr-only">Sobre a carteira de investimentos MyProfit</span>
              </button>
            </div>
            {portfolioInfoOpen ? <p id={portfolioInfoId} className="mt-2 max-w-xl text-xs leading-5 text-muted-foreground">Usa o snapshot disponível da sua carteira de investimentos para a data da simulação. Não representa seu patrimônio total.</p> : null}
          </div>
        ) : goalSourceMode === "selector" ? (
          <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
            Meta com valor atual
            <select
              required
              value={value.goalId}
              onChange={(event) => patch({ goalId: event.target.value })}
              className={inputClassName}
            >
              <option value="">Selecione uma meta</option>
              {goals.map((goal) => (
                <option key={goal.id} value={goal.id}>
                  {goal.name} · {GOAL_TYPE_LABELS[goal.goal_type]} · {GOAL_STATUS_LABELS[goal.status]}
                </option>
              ))}
            </select>
            {goals.length === 0 ? <span className="text-xs font-normal text-muted-foreground">Nenhuma meta disponível para esta origem.</span> : null}
          </label>
        ) : (
          <p className="self-end text-sm text-muted-foreground sm:col-span-2 xl:col-span-2">Usa o valor atual da meta selecionada acima.</p>
        )}

        <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
          Aporte mensal
          <input
            required
            value={value.monthlyContribution}
            onChange={(event) => patch({ monthlyContribution: event.target.value }, "monthlyContribution")}
            placeholder="Ex.: R$ 250,00"
            inputMode="decimal"
            aria-describedby={fieldErrors.monthlyContribution ? `${idPrefix}-contribution-error` : undefined}
            className={inputClassName}
          />
          <FieldError id={`${idPrefix}-contribution-error`} message={fieldErrors.monthlyContribution} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
          Retorno esperado ao ano
          <div className="relative">
            <input
              required
              aria-label="Retorno esperado ao ano"
              value={value.expectedReturnRate}
              onChange={(event) => patch({ expectedReturnRate: event.target.value }, "expectedReturnRate")}
              placeholder="Ex.: 8,5"
              inputMode="decimal"
              aria-describedby={fieldErrors.expectedReturnRate ? `${idPrefix}-return-error` : `${idPrefix}-return-help`}
              className={`${inputClassName} pr-14`}
            />
            <span aria-hidden="true" className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-muted-foreground">% a.a.</span>
          </div>
          <span id={`${idPrefix}-return-help`} className="text-xs font-normal text-muted-foreground">Ex.: 8,5 = 8,5% ao ano.</span>
          <FieldError id={`${idPrefix}-return-error`} message={fieldErrors.expectedReturnRate} />
        </label>
        {!comparisonScenario ? (
          <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
            Horizonte (meses)
            <input
              required
              type="number"
              aria-label="Horizonte (meses)"
              value={value.horizonMonths ?? ""}
              onChange={(event) => {
                const nextValue = event.currentTarget.valueAsNumber;
                patch({ horizonMonths: Number.isNaN(nextValue) ? undefined : nextValue }, "horizonMonths");
              }}
              aria-describedby={fieldErrors.horizonMonths ? `${idPrefix}-horizon-error` : undefined}
              className={inputClassName}
            />
            <FieldError id={`${idPrefix}-horizon-error`} message={fieldErrors.horizonMonths} />
          </label>
        ) : null}
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          aria-expanded={advancedOpen}
          aria-controls={advancedId}
          onClick={() => setAdvancedOpen((current) => !current)}
          className={`inline-flex flex-wrap items-center justify-end gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs font-medium text-violet-700 transition hover:bg-violet-300/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/50 dark:text-violet-300 ${
            hasNonDefaultConfiguration
              ? "border-violet-300/35 bg-violet-300/[0.08]"
              : "border-border bg-transparent"
          }`}
        >
          {comparisonScenario ? "Opções do cenário" : "Opções avançadas"}
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
            {basisSummary}
          </span>
          {!comparisonScenario && value.asOfDate ? <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">Data personalizada</span> : null}
          {showInflation && value.inflationRate ? <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">Inflação</span> : null}
          {value.observedAt ? <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">Patrimônio histórico</span> : null}
          <ChevronDown aria-hidden="true" size={14} className={advancedOpen ? "rotate-180 transition-transform" : "transition-transform"} />
        </button>
      </div>
      {advancedOpen ? (
        <div id={advancedId} className="grid gap-4 rounded-xl border border-border bg-muted/25 p-4 sm:grid-cols-2 xl:grid-cols-3">
          <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
            Tipo de retorno
            <select value={value.returnType} onChange={(event) => updateReturnType(event.target.value as ReturnType)} className={inputClassName}>
              <option value="NOMINAL">Nominal</option>
              <option value="REAL">Real</option>
            </select>
          </label>
          {!comparisonScenario ? (
            <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
              Base de saída
              <select value={value.outputMode} onChange={(event) => updateOutputMode(event.target.value as OutputMode)} className={inputClassName}>
                <option value="NOMINAL" disabled={value.returnType === "REAL"}>Nominal</option>
                <option value="REAL">Real</option>
              </select>
            </label>
          ) : null}
          {showInflation ? (
            <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
              Inflação esperada
              <div className="relative">
                <input
                  required
                  value={value.inflationRate}
                  onChange={(event) => patch({ inflationRate: event.target.value }, "inflationRate")}
                  placeholder="Ex.: 4"
                  inputMode="decimal"
                  aria-describedby={fieldErrors.inflationRate ? `${idPrefix}-inflation-error` : undefined}
                  className={`${inputClassName} pr-14`}
                />
                <span aria-hidden="true" className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-muted-foreground">% a.a.</span>
              </div>
              <FieldError id={`${idPrefix}-inflation-error`} message={fieldErrors.inflationRate} />
            </label>
          ) : null}
          {!comparisonScenario ? (
            <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
              Data-base personalizada
              <input
                value={value.asOfDate}
                onChange={(event) => patch({ asOfDate: event.target.value }, "asOfDate")}
                placeholder="DD/MM/AAAA"
                inputMode="numeric"
                aria-describedby={fieldErrors.asOfDate ? `${idPrefix}-as-of-error` : undefined}
                className={inputClassName}
              />
              <FieldError id={`${idPrefix}-as-of-error`} message={fieldErrors.asOfDate} />
              <button type="button" onClick={() => patch({ asOfDate: "" }, "asOfDate")} className="self-start text-xs font-medium text-violet-700 hover:text-violet-600 dark:text-violet-300 dark:hover:text-violet-200">Usar hoje</button>
            </label>
          ) : null}
          {value.source === "USER_PROVIDED_SCENARIO" ? (
            <label className="flex flex-col gap-1.5 text-sm font-medium text-foreground/90">
              Data e hora do patrimônio
              <input
                type="datetime-local"
                value={value.observedAt}
                onChange={(event) => patch({ observedAt: event.target.value }, "observedAt")}
                aria-describedby={fieldErrors.observedAt ? `${idPrefix}-observed-error` : undefined}
                className={inputClassName}
              />
              <span className="text-xs font-normal text-muted-foreground">Vazio usa o momento do envio.</span>
              <FieldError id={`${idPrefix}-observed-error`} message={fieldErrors.observedAt} />
              <button type="button" onClick={() => patch({ observedAt: "" }, "observedAt")} className="self-start text-xs font-medium text-violet-700 hover:text-violet-600 dark:text-violet-300 dark:hover:text-violet-200">Usar momento do envio</button>
            </label>
          ) : null}
          {advancedSlot}
          <p className="text-xs leading-5 text-muted-foreground sm:col-span-2 xl:col-span-3">Taxa efetiva anual · Aporte no fim do mês</p>
        </div>
      ) : null}
    </fieldset>
  );
}
