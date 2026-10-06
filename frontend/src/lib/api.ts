const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_BASE_URL) {
  throw new Error("Falta configurar a variável NEXT_PUBLIC_API_URL no .env.local");
}

export class AuthError extends Error {
  constructor() {
    super("Autenticação necessária");
    this.name = "AuthError";
  }
}

export class APIRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly endpoint: string,
  ) {
    super(`API request failed with status ${status}`);
    this.name = "APIRequestError";
  }
}

export async function requestFromAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("fin_token") : null;
  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders["Authorization"] = `Bearer ${token}`;
  }

  const isFormData = options.body instanceof FormData;
  const defaultHeaders: Record<string, string> = {};
  if (!isFormData) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const finalHeaders: Record<string, string> = {
    ...defaultHeaders,
    ...authHeaders,
  };
  if (options.headers) {
    const extraHeaders = options.headers as Record<string, string>;
    for (const [key, value] of Object.entries(extraHeaders)) {
      if (value !== undefined) finalHeaders[key] = value;
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: finalHeaders,
    cache: "no-store",
  });

  if (response.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("fin_token");
      window.location.href = "/login";
    }
    throw new AuthError();
  }

  if (!response.ok) {
    throw new APIRequestError(response.status, endpoint);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function fetchFromAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T | null> {
  try {
    return await requestFromAPI<T>(endpoint, options);
  } catch (error) {
    if (error instanceof AuthError) {
      throw error; // Let the caller handle 401
    }
    console.error(`[API FETCH ERROR] Falha ao aceder a ${endpoint}:`, error);
    return null;
  }
}
