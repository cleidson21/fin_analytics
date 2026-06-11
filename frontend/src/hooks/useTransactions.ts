"use client";

import { useState, useEffect, useCallback } from "react";
import { Transaction } from "@/types/entities";
import { PaginatedResponse } from "@/types/dto";
import { fetchFromAPI } from "@/lib/api";

export interface TransactionFilters {
  limit: number;
  offset: number;
  search?: string;
  startDate?: string;
  endDate?: string;
  category?: string;
}

export function useTransactions(filters: TransactionFilters) {
  const [data, setData] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      queryParams.set("limit", filters.limit.toString());
      queryParams.set("offset", filters.offset.toString());
      if (filters.search) queryParams.set("search", filters.search);
      if (filters.startDate) queryParams.set("startDate", filters.startDate);
      if (filters.endDate) queryParams.set("endDate", filters.endDate);
      if (filters.category) queryParams.set("category", filters.category);

      const response = await fetchFromAPI<PaginatedResponse<Transaction>>(
        `/transactions?${queryParams.toString()}`
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
    filters.search,
    filters.startDate,
    filters.endDate,
    filters.category,
  ]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  return {
    data,
    total,
    isLoading,
    error,
    refetch: fetchTransactions,
  };
}
