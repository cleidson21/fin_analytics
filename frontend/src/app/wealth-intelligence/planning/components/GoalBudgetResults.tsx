import type { GoalBudgetImpediment, GoalBudgetPreviewResponse } from "@/lib/planning";
import { formatAnnualRateDecimalString, formatBRDate, formatBRLDecimalString } from "@/lib/planningLocale";
import { PlanningStatusBadge } from "./PlanningResults";

const impediments: Record<GoalBudgetImpediment, string> = {
  TARGET_MISSING: "Valor-alvo não informado.",
  TARGET_NONPOSITIVE: "O valor-alvo cadastrado deve ser positivo.",
  CURRENT_AMOUNT_MISSING: "Valor atual não informado.",
  CURRENT_AMOUNT_NEGATIVE: "O valor atual cadastrado é negativo.",
};

function Money({ label, value }: { label: string; value: string | null }) {
  return <div className="min-w-0"><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 break-all font-medium tabular-nums text-foreground">{value === null ? "Não disponível" : formatBRLDecimalString(value)}</dd></div>;
}

export function GoalBudgetResults({ result }: { result: GoalBudgetPreviewResponse }) {
  return (
    <section aria-label="Resultado da distribuição de orçamento" className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="text-sm font-medium text-muted-foreground">Orçamento mensal</h3>
        <p className="mt-1 break-all text-2xl font-semibold tabular-nums text-foreground">{formatBRLDecimalString(result.monthly_budget)}</p>
        <p className="mt-2 text-xs text-muted-foreground">Valores nominais · {result.assumptions.horizon_months} meses · {formatAnnualRateDecimalString(result.assumptions.expected_return_rate)} · data-base {formatBRDate(result.assumptions.as_of_date)}</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {result.scenarios.map((scenario) => (
            <section key={scenario.scenario_id} aria-label={`Orçamento do cenário ${scenario.scenario_id}`} className="min-w-0 border-t border-border pt-3">
              <h4 className="mb-3 text-sm font-semibold">Cenário {scenario.scenario_id}</h4>
              <dl className="grid gap-3">
                <Money label="Total alocado" value={scenario.allocated_total} />
                <Money label="Não alocado" value={scenario.unallocated_amount} />
                {!/^-?0+(?:\.0+)?$/.test(scenario.exceeded_amount) ? <Money label="Excesso orçamentário" value={scenario.exceeded_amount} /> : null}
              </dl>
            </section>
          ))}
        </div>
      </div>
      {result.results.map((item) => (
        <article key={item.goal_id} aria-label={`Resultado de ${item.name}`} className="min-w-0 space-y-4 rounded-xl border border-border bg-card p-4">
          <h3 className="break-words text-base font-semibold text-foreground">{item.name}</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {result.scenarios.map((scenario) => {
              const allocation = scenario.allocations.find((entry) => entry.goal_id === item.goal_id);
              const entry = item.comparison?.entries.find((value) => value.scenario_id === scenario.scenario_id);
              const achievement = entry?.target_achievement_result;
              return (
                <section key={scenario.scenario_id} aria-label={`${item.name}, cenário ${scenario.scenario_id}`} className="min-w-0 space-y-3 border-t border-border pt-3">
                  <h4 className="text-sm font-semibold">Cenário {scenario.scenario_id}</h4>
                  <dl className="space-y-3 text-sm">
                    <Money label="Aporte mensal" value={allocation?.scenario_monthly_contribution ?? null} />
                    <Money label="Projeção ao final do horizonte" value={entry?.projection_result.final_wealth ?? null} />
                  </dl>
                  {achievement ? <div className="space-y-2 text-xs text-muted-foreground">
                    <PlanningStatusBadge status={achievement.status} neutral />
                    {achievement.months_required !== null ? <p>Meta em {achievement.months_required} meses{achievement.achievement_date ? ` · ${formatBRDate(achievement.achievement_date)}` : ""}</p> : null}
                  </div> : null}
                </section>
              );
            })}
          </div>
          {item.availability === "UNAVAILABLE" ? (
            <p role="status" className="text-sm text-warning-foreground">Dados insuficientes. {item.impediment_code ? impediments[item.impediment_code] : "Projeção não disponível."} Os aportes continuam incluídos no orçamento.</p>
          ) : item.comparison ? (() => {
            const alternative = item.comparison.entries.find((entry) => entry.scenario_id === "B");
            return alternative ? <section aria-label={`Diferenças de ${item.name}`} className="border-t border-border pt-3">
              <h4 className="mb-3 text-sm font-medium">Diferenças de B em relação a A</h4>
              <dl className="grid gap-3 text-sm sm:grid-cols-3">
                <Money label="Projeção final" value={alternative.final_wealth_delta} />
                <Money label="Aportes no horizonte" value={alternative.total_contributions_delta} />
                <Money label="Crescimento projetado" value={alternative.total_projected_growth_delta} />
              </dl>
              <p className="mt-3 text-xs text-muted-foreground">Antecipação da meta em B: {alternative.months_saved_or_lost === null ? "não disponível" : `${alternative.months_saved_or_lost} meses (positivo antecipa; negativo adia)`}.</p>
            </section> : null;
          })() : null}
          <details className="border-t border-border pt-3 text-xs text-muted-foreground">
            <summary className="cursor-pointer rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Dados cadastrais e origem</summary>
            <dl className="mt-3 grid gap-3 sm:grid-cols-2">
              <Money label="Valor-alvo cadastrado" value={item.target_amount} />
              <Money label="Valor atual cadastrado" value={item.current_amount} />
            </dl>
            <p className="mt-3">Origem: valor atual da própria meta, informado no cadastro; sem sincronização automática com investimentos.</p>
            {item.goal_updated_at ? <p className="mt-1">Cadastro atualizado em {formatBRDate(item.goal_updated_at.slice(0, 10))}.</p> : null}
          </details>
        </article>
      ))}
    </section>
  );
}
