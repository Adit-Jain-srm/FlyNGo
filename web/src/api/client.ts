/**
 * FlyNGo API Client
 * Uses VITE_API_URL (default: http://localhost:8000)
 */

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ApiRuleError {
  rule: string;
  message: string;
  field?: string;
  allowed?: any;
}

export class ApiError extends Error {
  status: number;
  data: ApiRuleError | { message: string };

  constructor(status: number, data: any) {
    super(data?.message || `HTTP error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }
    throw new ApiError(response.status, errorData);
  }

  return response.json();
}

export interface HealthResponse {
  status: string;
  counts: Record<string, number>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}
