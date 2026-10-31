import { APIRequestError, requestFromAPI } from "@/lib/api";

export const LEDGER_AUTHORIZATION_PENDING =
  "Autorização financeira pendente. Revise e ative a certificação pessoal local.";

export function isLedgerAuthorizationError(error: unknown): boolean {
  return error instanceof APIRequestError && error.status === 403;
}

// Financial failures must not turn into empty lists or successful mutations.
// A signal also enables api.ts's replacement-session response guard.
export async function requestLedgerFromAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    return await requestFromAPI<T>(endpoint, {
      ...options,
      signal: options.signal ?? new AbortController().signal,
    });
  } catch (error) {
    if (isLedgerAuthorizationError(error)) {
      (error as Error).message = LEDGER_AUTHORIZATION_PENDING;
    }
    throw error;
  }
}
