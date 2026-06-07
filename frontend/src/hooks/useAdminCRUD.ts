import { useState } from "react";
import { fetchFromAPI } from "@/lib/api";

export function useTransactionAdmin() {
  const [isUpdating, setIsUpdating] = useState(false);

  const updateTransaction = async (idEconomico: string, payload: any) => {
    setIsUpdating(true);
    try {
      await fetchFromAPI(`/governance/transactions/${idEconomico}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } finally {
      setIsUpdating(false);
    }
  };

  return { updateTransaction, isUpdating };
}

export function usePositionAdmin() {
  const [isUpdating, setIsUpdating] = useState(false);

  const updatePosition = async (ticker: string, dataSnapshot: string, payload: any) => {
    setIsUpdating(true);
    try {
      await fetchFromAPI(`/governance/positions/${ticker}/${dataSnapshot}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } finally {
      setIsUpdating(false);
    }
  };

  return { updatePosition, isUpdating };
}

export function useDividendAdmin() {
  const [isUpdating, setIsUpdating] = useState(false);

  const updateDividend = async (idEconomico: string, payload: any) => {
    setIsUpdating(true);
    try {
      await fetchFromAPI(`/governance/dividends/${idEconomico}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } finally {
      setIsUpdating(false);
    }
  };

  return { updateDividend, isUpdating };
}

export function useCategoryAdmin() {
  const [isMerging, setIsMerging] = useState(false);

  const mergeCategories = async (payload: { source_category: string; target_category: string }) => {
    setIsMerging(true);
    try {
      await fetchFromAPI(`/governance/categories/merge`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } finally {
      setIsMerging(false);
    }
  };

  return { mergeCategories, isMerging };
}
