import { useState, useEffect, useCallback } from "react";
import { fetchFromAPI } from "@/lib/api";

export interface DatabaseSummary {
  total_transactions: number;
  total_positions: number;
  total_dividends: number;
  total_evolutions: number;
  total_import_runs: number;
  runs_confirmed: number;
  runs_pending: number;
}

export interface TableStatus {
  table_name: string;
  row_count: number;
  status: string;
}

export interface DatabaseHealth {
  database: string;
  imports: string;
  wealth: string;
  staging: string;
}

export interface DatabaseIntegrity {
  orphan_runs: number;
  pending_staging: number;
  duplicate_transactions_suspects: number;
}

export interface VacuumEstimate {
  size_current_kb: number;
  estimated_post_vacuum_kb: number;
}

export interface VacuumResult {
  size_before_kb: number;
  size_after_kb: number;
  freed_space_kb: number;
}

export function useDatabaseAdmin() {
  const [summary, setSummary] = useState<{ data: DatabaseSummary | null; isLoading: boolean }>({ data: null, isLoading: true });
  const [tables, setTables] = useState<{ data: TableStatus[] | null; isLoading: boolean }>({ data: null, isLoading: true });
  const [health, setHealth] = useState<{ data: DatabaseHealth | null; isLoading: boolean }>({ data: null, isLoading: true });
  const [integrity, setIntegrity] = useState<{ data: DatabaseIntegrity | null; isLoading: boolean }>({ data: null, isLoading: true });
  const [isUnauthorized, setIsUnauthorized] = useState(false);

  const [vacuumEstimateMutation, setVacuumEstimateMutation] = useState<{ data: VacuumEstimate | null; isPending: boolean }>({ data: null, isPending: false });
  const [vacuumMutation, setVacuumMutation] = useState<{ data: VacuumResult | null; isPending: boolean; isSuccess: boolean }>({ data: null, isPending: false, isSuccess: false });
  const [recountMutation, setRecountMutation] = useState<{ isPending: boolean }>({ isPending: false });

  const loadData = useCallback(async () => {
    setSummary(s => ({ ...s, isLoading: true }));
    setTables(s => ({ ...s, isLoading: true }));
    setHealth(s => ({ ...s, isLoading: true }));
    setIntegrity(s => ({ ...s, isLoading: true }));
    setIsUnauthorized(false);

    try {
      const [sumRes, tabRes, healRes, intRes] = await Promise.all([
        fetchFromAPI<DatabaseSummary>("/governance/database/summary"),
        fetchFromAPI<TableStatus[]>("/governance/database/tables"),
        fetchFromAPI<DatabaseHealth>("/governance/database/health"),
        fetchFromAPI<DatabaseIntegrity>("/governance/database/integrity")
      ]);

      setSummary({ data: sumRes, isLoading: false });
      setTables({ data: tabRes, isLoading: false });
      setHealth({ data: healRes, isLoading: false });
      setIntegrity({ data: intRes, isLoading: false });
    } catch (err: any) {
      if (err.name === "AuthError") {
        setIsUnauthorized(true);
      } else {
        console.error(err);
      }
      setSummary(s => ({ ...s, isLoading: false }));
      setTables(s => ({ ...s, isLoading: false }));
      setHealth(s => ({ ...s, isLoading: false }));
      setIntegrity(s => ({ ...s, isLoading: false }));
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const estimateVacuum = async () => {
    setVacuumEstimateMutation({ data: null, isPending: true });
    try {
      const data = await fetchFromAPI<VacuumEstimate>("/governance/database/vacuum/estimate", { method: "POST" });
      setVacuumEstimateMutation({ data, isPending: false });
      return data;
    } catch (err: any) {
      console.error(err);
      setVacuumEstimateMutation({ data: null, isPending: false });
    }
  };

  const runVacuum = async () => {
    setVacuumMutation({ data: null, isPending: true, isSuccess: false });
    try {
      const data = await fetchFromAPI<VacuumResult>("/governance/database/vacuum", { method: "POST" });
      setVacuumMutation({ data, isPending: false, isSuccess: true });
      loadData();
      return data;
    } catch (err: any) {
      console.error(err);
      setVacuumMutation({ data: null, isPending: false, isSuccess: false });
    }
  };

  const runRecount = async () => {
    setRecountMutation({ isPending: true });
    try {
      await fetchFromAPI("/governance/database/recount", { method: "POST" });
      setRecountMutation({ isPending: false });
      loadData();
    } catch (err: any) {
      console.error(err);
      setRecountMutation({ isPending: false });
    }
  };

  return {
    summary,
    tables,
    health,
    integrity,
    isUnauthorized,
    vacuumEstimateMutation: { ...vacuumEstimateMutation, mutateAsync: estimateVacuum },
    vacuumMutation: { ...vacuumMutation, mutateAsync: runVacuum },
    recountMutation: { ...recountMutation, mutate: runRecount },
  };
}
