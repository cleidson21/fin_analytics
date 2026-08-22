/**
 * Tipos alinhados ao Domínio Canônico — FIN Analytics
 * Fonte: docs/29_DOMAIN_ENTITIES.md + docs/40_DTOS.md
 * 
 * REGRA: Estes tipos devem espelhar exatamente os DTOs do backend.
 * Nunca referenciar campos do Provider diretamente aqui.
 * 
 * COMPAT: Os aliases no final do arquivo existem apenas para não quebrar
 * componentes de governance ainda não migrados (serão removidos por VS).
 */

// ─── Enums ────────────────────────────────────────────────────────────────────

export type ProviderType = "PIERRE" | "MYPROFIT" | "CSV" | "YFINANCE" | "MANUAL";
export type AccountType = "BANK" | "CREDIT_CARD" | "INVESTMENT" | "LOAN" | "WALLET";
export type CurrencyCode = "BRL" | "USD" | "EUR";
export type UserRole = "ADMIN" | "VIEWER";
export type MovementType = "CREDIT" | "DEBIT";
export type TransactionType = "PURCHASE" | "TRANSFER" | "INCOME" | "REFUND" | "OTHER";
export type TransactionStatus = "PENDING" | "CONFIRMED" | "CANCELLED";
export type AssetType = "STOCK" | "FII" | "ETF" | "BOND" | "CRYPTO" | "FUND" | "OTHER";
export type IncomeType = "DIVIDEND" | "JCP" | "RENT" | "INTEREST";

// ─── Entidades de Response (alinhadas aos DTOs do backend) ────────────────────

export interface UserDTO {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface InstitutionSummaryDTO {
  id: string;
  name: string;
  code: string;
  logo_url: string | null;
}

export interface AccountDTO {
  id: string;
  external_id: string | null;
  provider: ProviderType;
  name: string;
  type: AccountType;
  subtype: string | null;
  currency_code: CurrencyCode;
  balance: number | null;
  balance_updated_at: string | null;
  institution: InstitutionSummaryDTO | null;
  is_active: boolean;
}

export interface CategorySummaryDTO {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  color: string | null;
}

export interface CategoryDTO {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  icon: string | null;
  color: string | null;
  is_system: boolean;
  children: CategoryDTO[];
}

export interface TagDTO {
  id: string;
  name: string;
  color: string | null;
}

export interface TransactionDTO {
  id: string;
  external_id: string | null;
  provider: ProviderType;
  account_id: string;
  account_name: string;
  amount: number;
  direction: MovementType;
  currency_code: CurrencyCode;
  description: string;
  category: CategorySummaryDTO | null;
  type: TransactionType;
  status: TransactionStatus;
  transaction_date: string;
  posted_date: string | null;
  is_recurring: boolean;
  installment_count: number | null;
  installment_current: number | null;
  tags: TagDTO[];
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthTokenDTO {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserDTO;
}

// ─── Paginação ────────────────────────────────────────────────────────────────

export interface PaginatedDTO<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

// ─── Aliases de compatibilidade (remover conforme cada VS migrar) ─────────────
// @deprecated — use TransactionDTO
export interface Transaction {
  id: string;
  description?: string;
  category?: string;
  amount?: number;
  transaction_date?: string;
  // campos usados pelos componentes admin
  descricao?: string;
  valor?: string | number;
  data?: string;
  categoria?: string;
  macro_categoria?: string;
  parcelamento?: string;
  observacao?: string;
  [key: string]: unknown;
}

// @deprecated — use CategoryDTO
// Nota: campos reais retornados pela API de governança de categorias
export interface Category {
  id: string;
  name: string;
  slug: string;
  // campos reais da API /governance/categories
  categoria: string;
  quantidade_transacoes: number;
  [key: string]: unknown;
}

// @deprecated — Use PositionResponseDTO when implemented
export interface Position {
  id?: string;
  ticker?: string;
  quantity?: number;
  // campos usados pelos componentes admin (API /governance/positions)
  classe_ativo?: string;
  nome?: string;
  quantidade?: string | number;
  preco_medio?: string | number;
  snapshot_date?: string;
  data_snapshot?: string;  // alias usado pelo PositionEditDialog
  observacao?: string;
  [key: string]: unknown;
}

// @deprecated — Use DividendResponseDTO when implemented
export interface Dividend {
  id?: string;
  ticker?: string;
  amount?: number;
  // campos usados pelos componentes admin (API /governance/dividends)
  id_economico?: string;  // usado pelo DividendEditDialog
  tipo_evento?: string;
  observacao?: string;
  valor?: string | number;
  data_pagamento?: string;
  [key: string]: unknown;
}

