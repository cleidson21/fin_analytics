"use client";

import { useState, useEffect, useCallback } from "react";
import { Position } from "@/types/entities";
import { PaginatedResponse } from "@/types/dto";
import { fetchFromAPI } from "@/lib/api";

export interface PositionFilters {
  limit: number;
  offset: number;
  ticker?: string;
  classe_ativo?: string;
  snapshot_date?: string;
}

export function usePositionsAdmin(filters: PositionFilters) {
  const [data, setData] = useState<Position[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPositions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      queryParams.set("limit", filters.limit.toString());
      queryParams.set("offset", filters.offset.toString());
      if (filters.ticker) queryParams.set("ticker", filters.ticker);
      if (filters.classe_ativo) queryParams.set("classe_ativo", filters.classe_ativo);
      if (filters.snapshot_date) queryParams.set("snapshot_date", filters.snapshot_date);

      const response = await fetchFromAPI<PaginatedResponse<Position>>(
        `/governance/positions?${queryParams.toString()}`
      );

      if (response) {
        setData(response.items || []);
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
    filters.classe_ativo,
    filters.snapshot_date,
  ]);

  useEffect(() => {
    fetchPositions();
  }, [fetchPositions]);

  return {
    data,
    total,
    isLoading,
    error,
    refetch: fetchPositions,
  };
}
