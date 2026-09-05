import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";

export interface AssetAllocation {
  asset_class: string;
  current_total: string;
  current_total_value: number;
}

export interface PositionDetail {
  ticker: string;
  asset_class: string;
  asset_subclass: string;
  quantidade: string;
  preco_medio: string;
  valor_investido: string;
  valor_atual: string;
  ganho: string;
  peso_percentual: string;
  quantidade_value?: number;
  preco_medio_value?: number;
  valor_investido_value?: number;
  valor_atual_value: number;
  ganho_value?: number | null;
  peso_percentual_value: number;
  has_market_value: boolean;
  market_data_provider?: string;
  market_price?: number;
}

import { WealthSummary } from "./usePortfolioData";

export function useAllocationData() {
  const [allocation, setAllocation] = useState<AssetAllocation[]>([]);
  const [positions, setPositions] = useState<PositionDetail[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setIsLoading(true);
      setIsError(false);
      try {
        const wealth = await fetchFromAPI<any>("/investments/dashboard/allocation");

        if (!mounted) return;

        if (wealth) {
          const allocMapped: AssetAllocation[] = (wealth.by_class || []).map((cls: any) => ({
            asset_class: cls.name || "N/A",
            current_total: String(cls.market_value || 0),
            current_total_value: Number(cls.market_value || 0)
          }));

          const posMapped: PositionDetail[] = (wealth.by_asset || []).map((asset: any) => {
            const has_market_value = asset.has_market_value === true;
            const effective_current_value = has_market_value ? Number(asset.market_value) : Number(asset.invested_value || 0);

            return {
              ticker: asset.name || "N/A",
              asset_class: asset.asset_class || "N/A",
              asset_subclass: "N/A",
              quantidade: String(asset.quantity || 0),
              preco_medio: String(asset.avg_price || 0),
              valor_investido: String(asset.invested_value || 0),
              valor_atual: String(asset.market_value || 0),
              ganho: String(asset.profit || 0),
              peso_percentual: String(asset.allocation_percent || 0),
              quantidade_value: Number(asset.quantity || 0),
              preco_medio_value: Number(asset.avg_price || 0),
              valor_investido_value: Number(asset.invested_value || 0),
              valor_atual_value: effective_current_value,
              ganho_value: has_market_value ? Number(asset.profit) : null,
              peso_percentual_value: Number(asset.allocation_percent || 0),
              has_market_value,
              market_data_provider: asset.market_data_provider,
              market_price: asset.market_price ? Number(asset.market_price) : undefined
            };
          });

          setAllocation(allocMapped);
          setPositions(posMapped);
        } else {
          setIsError(true);
        }
      } catch {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, []);

  const totalAssets = positions.length;
  
  // Sort positions by value desc
  const sortedPositions = [...positions].sort((a, b) => b.valor_atual_value - a.valor_atual_value);
  const top5 = sortedPositions.slice(0, 5);
  
  const totalValue = positions.reduce((acc, p) => acc + p.valor_atual_value, 0);
  const top5Value = top5.reduce((acc, p) => acc + p.valor_atual_value, 0);
  const top5Concentration = totalValue > 0 ? (top5Value / totalValue) * 100 : 0;

  let dominantClass = { name: "N/A", percentage: 0 };
  if (allocation.length > 0 && totalValue > 0) {
    const sortedAlloc = [...allocation].sort((a, b) => b.current_total_value - a.current_total_value);
    dominantClass = {
      name: sortedAlloc[0].asset_class,
      percentage: (sortedAlloc[0].current_total_value / totalValue) * 100
    };
  }

  // Very simple diversification score: penalizes high top-5 concentration and rewards number of assets
  const calcScore = () => {
    if (totalAssets === 0) return 0;
    let score = 100;
    // penalty for top 5 concentration > 30%
    if (top5Concentration > 30) {
      score -= (top5Concentration - 30) * 1.5; 
    }
    // penalty for few assets
    if (totalAssets < 10) score -= (10 - totalAssets) * 2;
    return Math.max(0, Math.min(100, Math.round(score)));
  };

  const diversificationScore = calcScore();

  return {
    allocation,
    positions: sortedPositions,
    top5,
    top5Concentration,
    totalAssets,
    dominantClass,
    diversificationScore,
    isLoading,
    isError
  };
}
