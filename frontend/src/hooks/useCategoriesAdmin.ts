"use client";

import { useState, useEffect, useCallback } from "react";
import { Category } from "@/types/entities";
import { PaginatedResponse } from "@/types/dto";
import { fetchFromAPI } from "@/lib/api";

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

      const response = await fetchFromAPI<PaginatedResponse<Category>>(
        `/governance/categories?${queryParams.toString()}`
      );

      if (response && response.data) {
        let filteredItems = response.data;
        
        // Fase 5 - Busca Local (Frontend)
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          filteredItems = response.data.filter((item: Category) =>
            item.categoria.toLowerCase().includes(searchLower)
          );
        }

        setData(filteredItems);
        // Quando tem busca, o total é o tamanho da lista filtrada. 
        // Quando não tem, usa o total do backend.
        setTotal(filters.search ? filteredItems.length : response.total || 0);
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
