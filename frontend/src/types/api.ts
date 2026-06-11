export interface APIError extends Error {
  status?: number;
  code?: string;
}
