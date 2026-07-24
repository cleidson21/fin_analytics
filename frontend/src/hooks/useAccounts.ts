"use client";

import { useEffect, useState } from "react";
import { fetchFromAPI } from "@/lib/api";
import { AccountDTO } from "@/types/entities";

/**
 * Hook: useAccounts
 * Vertical Slice: VS-02
 * Endpoint: GET /accounts
 * Spec: docs/37_USE_CASES.md (UC-11A GetAccounts)
 */
export function useAccounts(params?: { is_active?: boolean; type?: string }) {
  const [data, setData] = useState<AccountDTO[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAccounts = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const queryParams = new URLSearchParams();
        if (params?.is_active !== undefined)
          queryParams.set("is_active", String(params.is_active));
        if (params?.type) queryParams.set("type", params.type);

        const qs = queryParams.toString();
        const result = await fetchFromAPI<AccountDTO[]>(
          `/accounts${qs ? `?${qs}` : ""}`
        );
        setData(result ?? []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar contas");
        setData([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAccounts();
  }, [params?.is_active, params?.type]);

  return { data, isLoading, error };
}
