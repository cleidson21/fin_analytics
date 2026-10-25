"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { useAuth } from "@/contexts/AuthContext";

import {
  isSelectableAnalysis,
  type TransientAnalysisCandidate,
  type TransientAnalysisSelection,
} from "./transientAnalysis";

type OwnedSelection = {
  ownerUserId: string;
  ownerToken: string;
  selection: TransientAnalysisSelection;
};

type TransientAnalysisContextValue = {
  selection: TransientAnalysisSelection | null;
  selectAnalysis: (candidate: TransientAnalysisCandidate) => boolean;
  clearSelection: () => void;
};

const TransientAnalysisContext = createContext<TransientAnalysisContextValue | null>(null);

export function TransientAnalysisProvider({ children }: { children: ReactNode }) {
  const { user, token, isLoading } = useAuth();
  const [ownedSelection, setOwnedSelection] = useState<OwnedSelection | null>(null);
  const userId = user?.id ?? null;

  const selection =
    ownedSelection !== null &&
    userId !== null &&
    token !== null &&
    ownedSelection.ownerUserId === userId &&
    ownedSelection.ownerToken === token
      ? ownedSelection.selection
      : null;

  useEffect(() => {
    if (ownedSelection === null) return;
    if (
      userId === null ||
      token === null ||
      ownedSelection.ownerUserId !== userId ||
      ownedSelection.ownerToken !== token
    ) {
      setOwnedSelection(null);
    }
  }, [ownedSelection, token, userId]);

  const selectAnalysis = useCallback(
    (candidate: TransientAnalysisCandidate) => {
      if (isLoading || userId === null || token === null || !isSelectableAnalysis(candidate)) {
        return false;
      }
      setOwnedSelection({
        ownerUserId: userId,
        ownerToken: token,
        selection: {
          ...candidate,
          selectedAt: new Date().toISOString(),
          validation: "VALIDATED_API_RESPONSE",
        } as TransientAnalysisSelection,
      });
      return true;
    },
    [isLoading, token, userId],
  );

  const clearSelection = useCallback(() => setOwnedSelection(null), []);
  const value = useMemo(
    () => ({ selection, selectAnalysis, clearSelection }),
    [clearSelection, selectAnalysis, selection],
  );

  return (
    <TransientAnalysisContext.Provider value={value}>
      {children}
    </TransientAnalysisContext.Provider>
  );
}

export function useTransientAnalysis() {
  const context = useContext(TransientAnalysisContext);
  if (context === null) {
    throw new Error("useTransientAnalysis must be used within TransientAnalysisProvider");
  }
  return context;
}
