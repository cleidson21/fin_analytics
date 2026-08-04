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

export async function fetchFromAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T | null> {
  try {
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
    // Merge options.headers cuidadosamente
    if (options.headers) {
      const extraHeaders = options.headers as Record<string, string>;
      for (const [k, v] of Object.entries(extraHeaders)) {
        if (v !== undefined) finalHeaders[k] = v;
      }
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: finalHeaders,
      cache: "no-store", // Vital para dashboards em tempo real
    });

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
      throw new AuthError();
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof AuthError) {
      throw error; // Let the caller handle 401
    }
    console.error(`[API FETCH ERROR] Falha ao aceder a ${endpoint}:`, error);
    return null;
  }
}
