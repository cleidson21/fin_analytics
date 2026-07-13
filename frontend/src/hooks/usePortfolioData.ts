import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";

export interface WealthSummary {
  total_cost_basis: number;
  total_market_value: number;
  total_unrealized_gain: number;
  total_unrealized_gain_percent: number;
  asset_count: number;
  by_institution: any[];
  by_class: any[];
  by_asset: any[];
}

export function usePortfolioData() {
  const [data, setData] = useState<WealthSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const res = await fetchFromAPI<WealthSummary>("/investments/portfolio");
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
