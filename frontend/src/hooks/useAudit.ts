import { useState, useEffect } from "react";
import { fetchFromAPI } from "@/lib/api";
import { requestLedgerFromAPI } from "@/lib/ledgerApi";

export interface AuditRun {
  id: string;
  file_name: string;
  source_type: string;
  started_at: string;
  status: string;
  created_by: string;
  rows_read: number;
  rows_inserted: number;
  rows_updated: number;
  rows_failed: number;
}

export interface AuditRollback {
  id: string;
  file_name: string;
  rollback_timestamp: string | null;
  rollback_user: string | null;
  rollback_reason: string | null;
  started_at: string;
}

export function useAuditRuns(filter: string = "ALL") {
  const [data, setData] = useState<AuditRun[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUnauthorized, setIsUnauthorized] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchRuns = async () => {
      setIsLoading(true);
      setIsUnauthorized(false);
      try {
        const result = await fetchFromAPI<AuditRun[]>(`/governance/audit?status_filter=${filter}`);
        if (mounted) {
          setData(result);
          setIsLoading(false);
        }
      } catch (e: unknown) {
        if (mounted) {
          if (e instanceof Error && e.name === "AuthError") {
            setIsUnauthorized(true);
          } else {
            console.error(e);
            setData([]);
          }
          setIsLoading(false);
        }
      }
    };
    fetchRuns();
    return () => { mounted = false; };
  }, [filter]);

  return { data, isLoading, isUnauthorized };
}

export function useAuditRollbacks() {
  const [data, setData] = useState<AuditRollback[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUnauthorized, setIsUnauthorized] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchRollbacks = async () => {
      setIsLoading(true);
      setIsUnauthorized(false);
      try {
        const result = await fetchFromAPI<AuditRollback[]>("/governance/audit/rollbacks");
        if (mounted) {
          setData(result);
          setIsLoading(false);
        }
      } catch (e: unknown) {
        if (mounted) {
          if (e instanceof Error && e.name === "AuthError") {
            setIsUnauthorized(true);
          } else {
            console.error(e);
            setData([]);
          }
          setIsLoading(false);
        }
      }
    };
    fetchRollbacks();
    return () => { mounted = false; };
  }, []);

  return { data, isLoading, isUnauthorized };
}

export function useAuditRunDetail(runId: string) {
  const [data, setData] = useState<AuditRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUnauthorized, setIsUnauthorized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetchRun = async () => {
      setIsLoading(true);
      setIsUnauthorized(false);
      setError(null);
      try {
        const result = await requestLedgerFromAPI<AuditRun>(`/governance/imports/${runId}`);
        if (mounted) {
          setData(result);
          setIsLoading(false);
        }
      } catch (e: unknown) {
        if (mounted) {
          setData(null);
          if (e instanceof Error && e.name === "AuthError") {
            setIsUnauthorized(true);
          } else {
            setError(e instanceof Error ? e.message : "Falha ao carregar importação");
          }
          setIsLoading(false);
        }
      }
    };
    if (runId) {
      fetchRun();
    }
    return () => { mounted = false; };
  }, [runId]);

  return { data, isLoading, isUnauthorized, error };
}
