/**
 * DTOs de Request/Response — FIN Analytics
 * Alinhados ao contrato do backend (docs/40_DTOS.md)
 * 
 * NOTE: PaginatedDTO genérico movido para types/entities.ts.
 * Este arquivo mantém apenas DTOs de Request (Write operations).
 */

// ─── Re-export para compatibilidade ──────────────────────────────────────────
export type { PaginatedDTO as PaginatedResponse } from "./entities";

// ─── Requests ─────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UpdateCategoryRequest {
  category_id: string;
}

// ─── Aliases legados (remover conforme VS migrar os hooks de admin) ────────────
// @deprecated
export interface UpdateTransactionDTO {
  category_id?: string;
  [key: string]: unknown;
}

// @deprecated
export interface UpdatePositionDTO {
  [key: string]: unknown;
}

// @deprecated
export interface UpdateDividendDTO {
  [key: string]: unknown;
}
