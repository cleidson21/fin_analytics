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

export const GOAL_TYPE_LABELS: Record<GoalType, string> = {
  EMERGENCY_RESERVE: "Reserva de Emergência",
  RETIREMENT: "Aposentadoria",
  TRAVEL: "Viagem",
  PURCHASE: "Compra",
  CUSTOM: "Personalizada",
  WEALTH_TARGET: "Patrimônio-Alvo",
  INVESTMENT_TARGET: "Investimento-Alvo",
  DIVIDEND_INCOME: "Renda de Dividendos",
  FINANCIAL_INDEPENDENCE: "Independência Financeira",
};

export const GOAL_STATUS_LABELS: Record<GoalStatus, string> = {
  ACTIVE: "Ativa",
  PAUSED: "Pausada",
  ACHIEVED: "Concluída",
  CANCELLED: "Cancelada",
};

export const GOAL_TYPE_OPTIONS: { value: GoalType; label: string }[] = [
  { value: "EMERGENCY_RESERVE", label: GOAL_TYPE_LABELS.EMERGENCY_RESERVE },
  { value: "TRAVEL", label: GOAL_TYPE_LABELS.TRAVEL },
  { value: "PURCHASE", label: GOAL_TYPE_LABELS.PURCHASE },
  { value: "WEALTH_TARGET", label: GOAL_TYPE_LABELS.WEALTH_TARGET },
  { value: "INVESTMENT_TARGET", label: GOAL_TYPE_LABELS.INVESTMENT_TARGET },
  { value: "DIVIDEND_INCOME", label: GOAL_TYPE_LABELS.DIVIDEND_INCOME },
  { value: "FINANCIAL_INDEPENDENCE", label: GOAL_TYPE_LABELS.FINANCIAL_INDEPENDENCE },
  { value: "RETIREMENT", label: GOAL_TYPE_LABELS.RETIREMENT },
  { value: "CUSTOM", label: GOAL_TYPE_LABELS.CUSTOM },
];

export const GOAL_STATUS_OPTIONS: { value: GoalStatus; label: string }[] = [
  { value: "ACTIVE", label: GOAL_STATUS_LABELS.ACTIVE },
  { value: "PAUSED", label: GOAL_STATUS_LABELS.PAUSED },
  { value: "ACHIEVED", label: GOAL_STATUS_LABELS.ACHIEVED },
  { value: "CANCELLED", label: GOAL_STATUS_LABELS.CANCELLED },
];
