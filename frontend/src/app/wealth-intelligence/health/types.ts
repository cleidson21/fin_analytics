export type DecimalString = string;

export interface CashflowSummary {
  reference_month: string;
  total_income: DecimalString;
  total_expense: DecimalString;
  net_cashflow: DecimalString;
  savings_amount: DecimalString;
  savings_rate: DecimalString | null;
  average_monthly_income: DecimalString | null;
  average_monthly_expense: DecimalString | null;
  average_monthly_net_cashflow: DecimalString | null;
}

export interface HistoricalFinancialMetric {
  reference_month: string;
  total_income: DecimalString;
  total_expense: DecimalString;
  net_cashflow: DecimalString;
  savings_amount: DecimalString;
  savings_rate: DecimalString | null;
}

export interface CategoryExpenseMetric {
  category: string;
  expense_total: DecimalString;
  share_of_expenses: DecimalString | null;
  rank: number;
}

export interface CategoryExpenseSummary {
  reference_month: string;
  total_expense: DecimalString;
  categories: CategoryExpenseMetric[];
  top_category: CategoryExpenseMetric | null;
}

export type SpendingAnomalyStatus =
  | "NORMAL"
  | "SPIKE"
  | "NEW_EXPENSE"
  | "INSUFFICIENT_HISTORY"
  | "BELOW_BASELINE_FLOOR"
  | "NEW_EXPENSE_BELOW_THRESHOLD";

export type SpendingAnomalyGlobalStatus = "OK" | "INSUFFICIENT_BASELINE";

export interface SpendingAnomalyEvaluation {
  category: string;
  status: SpendingAnomalyStatus;
  current_expense: DecimalString;
  baseline_values: DecimalString[];
  baseline_months_used: string[];
  baseline_reference: DecimalString | null;
  ratio: DecimalString | null;
  ratio_threshold: DecimalString | null;
  baseline_floor: DecimalString | null;
  new_expense_threshold: DecimalString | null;
}

export interface SpendingAnomalySummary {
  target_reference_month: string;
  global_status: SpendingAnomalyGlobalStatus;
  evaluations: SpendingAnomalyEvaluation[];
  anomalies: SpendingAnomalyEvaluation[];
}

export type FinancialTrendDirection =
  | "INCREASED"
  | "DECREASED"
  | "UNCHANGED"
  | "INSUFFICIENT_DATA";

export type CategoryTrendDirection =
  | FinancialTrendDirection
  | "NEW"
  | "DISAPPEARED";

export type FinancialTrendSummaryStatus = "OK" | "INSUFFICIENT_DATA";

export interface GlobalFinancialTrendMetric {
  metric: "total_income" | "total_expense" | "net_cashflow" | "savings_rate";
  current_value: DecimalString | null;
  previous_value: DecimalString | null;
  absolute_delta: DecimalString | null;
  percentage_delta: DecimalString | null;
  direction: FinancialTrendDirection;
}

export interface GlobalFinancialTrendSummary {
  status: FinancialTrendSummaryStatus;
  metrics: GlobalFinancialTrendMetric[];
}

export interface CategoryFinancialTrend {
  category: string;
  current_expense: DecimalString | null;
  previous_expense: DecimalString | null;
  absolute_delta: DecimalString | null;
  percentage_delta: DecimalString | null;
  direction: CategoryTrendDirection;
}

export interface CategoryFinancialTrendSummary {
  status: FinancialTrendSummaryStatus;
  items: CategoryFinancialTrend[];
}

export interface FinancialTrendResponse {
  requested_reference_month: string;
  trend_target_month: string;
  comparison_month: string;
  status: FinancialTrendSummaryStatus;
  global: GlobalFinancialTrendSummary;
  categories: CategoryFinancialTrendSummary;
}
