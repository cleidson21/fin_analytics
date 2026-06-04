import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";

export interface AssetAllocation {
  asset_class: string;
  current_total: string;
  current_total_value: number;
}

export interface PositionDetail {
  ticker: string;
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
  ganho_value?: number;
  peso_percentual_value: number;
}

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
        const [allocRes, posRes] = await Promise.all([
          fetchFromAPI<AssetAllocation[]>("/investments/allocation"),
          fetchFromAPI<PositionDetail[]>("/investments/positions")
        ]);

        if (!mounted) return;

        if (allocRes && posRes) {
          setAllocation(allocRes);
          setPositions(posRes);
        } else {
          setIsError(true);
        }
      } catch (err) {
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
