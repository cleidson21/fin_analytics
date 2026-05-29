const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_BASE_URL) {
  throw new Error("Falta configurar a variável NEXT_PUBLIC_API_URL no .env.local");
}

export async function fetchFromAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      cache: "no-store", // Vital para dashboards em tempo real
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    console.error(`[API FETCH ERROR] Falha ao aceder a ${endpoint}:`, error);
    return null;
  }
}
