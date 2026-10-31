"use client";

import { useState, useEffect, useCallback } from "react";
import { Category } from "@/types/entities";
import { requestLedgerFromAPI as fetchFromAPI } from "@/lib/ledgerApi";

export interface CategoryFilters {
  limit: number;
  offset: number;
  search?: string;
}

export function useCategoriesAdmin(filters: CategoryFilters) {
  const [data, setData] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchCategories = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      queryParams.set("limit", filters.limit.toString());
      queryParams.set("offset", filters.offset.toString());

      const response = await fetchFromAPI<{ provider: string; name: string; normalized_name?: string; transaction_count: number }[]>(
        `/categories?${queryParams.toString()}`
      );

      if (response) {
        let filteredItems = response.map((item) => ({
          ...item, id: `${item.provider}::${item.name}`, categoria: item.name,
          slug: item.normalized_name ?? item.name, quantidade_transacoes: item.transaction_count,
        }));
        
        // Fase 5 - Busca Local (Frontend)
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          filteredItems = filteredItems.filter((item: Category) =>
            item.categoria.toLowerCase().includes(searchLower)
          );
        }

        setData(filteredItems.slice(filters.offset, filters.offset + filters.limit));
        // Quando tem busca, o total é o tamanho da lista filtrada. 
        // Quando não tem, usa o total do backend.
        setTotal(filteredItems.length);
      }
    } catch (err: unknown) {
      if (err instanceof Error) setError(err);
      setData([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [filters.limit, filters.offset, filters.search]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  return {
    data,
    total,
    isLoading,
    error,
    refetch: fetchCategories,
  };
}
