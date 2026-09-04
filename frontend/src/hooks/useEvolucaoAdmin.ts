"use client";

import { useState, useEffect, useCallback } from "react";
import { PaginatedResponse } from "@/types/dto";
import { fetchFromAPI } from "@/lib/api";

export interface Evolucao {
  account_id: string;
  reference_month: string;
  patrimonio: number | null;
  pct_mensal: number | null;
  pct_acumulada: number | null;
  compras: number | null;
  vendas: number | null;
  op_finalizadas: number | null;
  proventos: number | null;
  ibov_mensal: number | null;
  ibov_acumulado: number | null;
  cdi_mensal: number | null;
  cdi_acumulado: number | null;
  ipca_mensal: number | null;
  ipca_acumulado: number | null;
  ifix_mensal: number | null;
  ifix_acumulado: number | null;
  sp_mensal: number | null;
  sp_acumulado: number | null;
  idiv_mensal: number | null;
  idiv_acumulado: number | null;
}

export interface EvolucaoFilters {
  limit: number;
  offset: number;
  account_id?: string;
}

export function useEvolucaoAdmin(filters: EvolucaoFilters) {
  const [data, setData] = useState<Evolucao[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchEvolucao = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      queryParams.set("limit", filters.limit.toString());
      queryParams.set("offset", filters.offset.toString());
      if (filters.account_id) queryParams.set("account_id", filters.account_id);

      const response = await fetchFromAPI<PaginatedResponse<Evolucao>>(
        `/governance/data/evolution?${queryParams.toString()}`
      );

      if (response) {
        setData(response.data || []);
        setTotal(response.total || 0);
      }
    } catch (err: unknown) {
      if (err instanceof Error) setError(err);
      setData([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [filters.limit, filters.offset, filters.account_id]);

  useEffect(() => {
    fetchEvolucao();
  }, [fetchEvolucao]);

  return {
    data,
    total,
    isLoading,
    error,
    refetch: fetchEvolucao,
  };
}
