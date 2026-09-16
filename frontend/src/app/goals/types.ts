// Types compartilhados do módulo Goals

export type GoalType =
  | "EMERGENCY_RESERVE"
  | "RETIREMENT"
  | "TRAVEL"
  | "PURCHASE"
  | "CUSTOM"
  | "WEALTH_TARGET"
  | "INVESTMENT_TARGET"
  | "DIVIDEND_INCOME"
  | "FINANCIAL_INDEPENDENCE";

export type GoalStatus = "ACTIVE" | "PAUSED" | "ACHIEVED" | "CANCELLED";

export type GoalPriority = 1 | 2 | 3 | 4 | 5;

export interface Goal {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  goal_type: GoalType;
  target_amount: number;
  target_date?: string | null;
  status: GoalStatus;
  current_amount?: number | null;
  priority?: GoalPriority | null;
  monthly_contribution?: number | null;
  linked_account_id?: string | null;
  assumptions_json?: string | null;
  progress_pct?: number | null;
  created_at: string;
  updated_at: string;
}

export interface GoalCreatePayload {
  name: string;
  description?: string;
  goal_type: GoalType;
  target_amount: number;
  target_date?: string;
  current_amount?: number;
  priority?: number;
  monthly_contribution?: number;
  linked_account_id?: string;
}

export interface GoalUpdatePayload {
  name?: string;
  description?: string;
  goal_type?: GoalType;
  target_amount?: number;
  target_date?: string;
  status?: GoalStatus;
  current_amount?: number;
  priority?: number;
  monthly_contribution?: number;
  linked_account_id?: string;
}

export const GOAL_TYPE_OPTIONS: { value: GoalType; label: string }[] = [
  { value: "EMERGENCY_RESERVE",   label: "Reserva de Emergência" },
  { value: "TRAVEL",              label: "Viagem" },
  { value: "PURCHASE",            label: "Compra" },
  { value: "WEALTH_TARGET",       label: "Patrimônio-Alvo" },
  { value: "INVESTMENT_TARGET",   label: "Investimento-Alvo" },
  { value: "DIVIDEND_INCOME",     label: "Renda de Dividendos" },
  { value: "FINANCIAL_INDEPENDENCE", label: "Independência Financeira" },
  { value: "RETIREMENT",          label: "Aposentadoria" },
  { value: "CUSTOM",              label: "Personalizada" },
];

export const GOAL_STATUS_OPTIONS: { value: GoalStatus; label: string }[] = [
  { value: "ACTIVE",    label: "Ativa" },
  { value: "PAUSED",    label: "Pausada" },
  { value: "ACHIEVED",  label: "Concluída" },
  { value: "CANCELLED", label: "Cancelada" },
];
