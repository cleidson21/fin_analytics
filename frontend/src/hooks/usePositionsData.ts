import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";

export interface ValuationResult {
  ticker: string;
  institution: string;
  quantity: number;
  cost_basis: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_gain: number;
  unrealized_gain_percent: number;
}

export function usePositionsData() {
  const [data, setData] = useState<ValuationResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const res = await fetchFromAPI<ValuationResult[]>("/investments/positions");
        if (!mounted) return;
        if (res) setData(res);
        else setIsError(true);
      } catch {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, []);

  return { data, isLoading, isError };
}
