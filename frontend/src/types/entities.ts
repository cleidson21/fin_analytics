export interface Transaction {
  id: string;
  descricao?: string;
  categoria?: string;
  category?: string; // Fallback used in some places
  macro_categoria: string;
  parcelamento: string;
  observacao?: string;
  data_transacao?: string;
  valor?: number;
  valor_cents?: number;
}

export interface Position {
  ticker: string;
  classe_ativo?: string;
  asset_class?: string; // Fallback
  observacao?: string;
  data_snapshot?: string;
  snapshot_date?: string; // Fallback
  quantidade: number;
  valor_investido: number;
  valor_atual: number;
  ganho: number;
  peso: number;
}

export interface Dividend {
  id_economico: string;
  ticker: string;
  tipo_evento?: string;
  tipo?: string; // Fallback
  observacao?: string;
  valor?: number;
  data_pagamento?: string;
  data?: string; // Fallback
}

export interface Category {
  categoria: string;
  macro_categoria?: string;
  quantidade_transacoes?: number;
}

export interface Installment {
  purchase_id: string;
  current_installment: number;
  total_installments: number;
  amount: number;
}

export interface AuditRun {
  id?: string;
  run_id?: string;
  file_name?: string;
  started_at: string;
  created_by?: string;
  source_type?: string;
  rows_read?: number;
  rows_inserted?: number;
  rows_updated?: number;
  rows_failed?: number;
  status: string;
}

export interface PortfolioEvolution {
  patrimonio_atual_value: number;
  rentabilidade_acumulada: number;
  compras_totais: number;
  cdi_acumulado_pct: number;
  history?: PortfolioEvolutionPoint[];
}

export interface PortfolioEvolutionPoint {
  month: string;
  patrimonio_value: number;
  compras_value: number;
  proventos_value: number;
  rentabilidade_mensal_pct: number;
}

export interface DatabaseSummary {
  total_tables: number;
  total_size: string;
  total_records: number;
  last_vacuum?: string;
}
