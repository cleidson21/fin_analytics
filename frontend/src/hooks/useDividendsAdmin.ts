"use client";

import { useState, useEffect, useCallback } from "react";
import { Dividend } from "@/types/entities";
import { PaginatedResponse } from "@/types/dto";
import { fetchFromAPI } from "@/lib/api";

export interface DividendFilters {
  limit: number;
  offset: number;
  ticker?: string;
  tipo_evento?: string;
  start_date?: string;
  end_date?: string;
}

export function useDividendsAdmin(filters: DividendFilters) {
  const [data, setData] = useState<Dividend[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchDividends = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      queryParams.set("limit", filters.limit.toString());
      queryParams.set("offset", filters.offset.toString());
      if (filters.ticker) queryParams.set("ticker", filters.ticker);
      if (filters.tipo_evento) queryParams.set("tipo_evento", filters.tipo_evento);
      if (filters.start_date) queryParams.set("start_date", filters.start_date);
      if (filters.end_date) queryParams.set("end_date", filters.end_date);

      const response = await fetchFromAPI<PaginatedResponse<Dividend>>(
        `/governance/dividends?${queryParams.toString()}`
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
  }, [
    filters.limit,
    filters.offset,
    filters.ticker,
    filters.tipo_evento,
    filters.start_date,
    filters.end_date,
  ]);

  useEffect(() => {
    fetchDividends();
  }, [fetchDividends]);

  return {
    data,
    total,
    isLoading,
    error,
    refetch: fetchDividends,
  };
}
