"use client";

/**
 * Hook: useTransactions
 * Status: PENDENTE — será implementado na Vertical Slice VS-04.
 * 
 * Endpoint: GET /transactions
 * Spec: docs/37_USE_CASES.md (UC-04 GetTransactions)
 */

// Stub vazio para não quebrar imports existentes durante a auditoria.
// NÃO fazer chamadas de API aqui até VS-04 ser implementada.

export interface TransactionFilters {
  limit: number;
  offset: number;
  search?: string;
  startDate?: string;
  endDate?: string;
  category?: string;
}

export function useTransactions(_filters: TransactionFilters) {
  return {
    data: [],
    total: 0,
    isLoading: false,
    error: null,
    refetch: () => Promise.resolve(),
  };
}
