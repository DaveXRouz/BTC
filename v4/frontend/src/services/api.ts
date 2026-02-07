/**
 * NPS V4 API client — typed fetch wrappers for all endpoints.
 */

const API_BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // TODO: Add JWT token from auth state
  // const token = getAuthToken();
  // if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ─── Health ───

export const health = {
  check: () => request<{ status: string; version: string }>("/health"),
  ready: () =>
    request<{ status: string; checks: Record<string, string> }>(
      "/health/ready",
    ),
};

// ─── Scanner ───

export const scanner = {
  start: (config: import("@/types").ScanConfig) =>
    request<import("@/types").ScanSession>("/scanner/start", {
      method: "POST",
      body: JSON.stringify(config),
    }),
  stop: (sessionId: string) =>
    request(`/scanner/stop/${sessionId}`, { method: "POST" }),
  pause: (sessionId: string) =>
    request(`/scanner/pause/${sessionId}`, { method: "POST" }),
  resume: (sessionId: string) =>
    request(`/scanner/resume/${sessionId}`, { method: "POST" }),
  stats: (sessionId: string) =>
    request<import("@/types").ScanStats>(`/scanner/stats/${sessionId}`),
  terminals: () =>
    request<{ terminals: import("@/types").ScanSession[] }>(
      "/scanner/terminals",
    ),
};

// ─── Oracle ───

export const oracle = {
  reading: (datetime?: string) =>
    request<import("@/types").OracleReading>("/oracle/reading", {
      method: "POST",
      body: JSON.stringify({ datetime }),
    }),
  question: (question: string) =>
    request<import("@/types").QuestionResponse>("/oracle/question", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  name: (name: string) =>
    request<import("@/types").NameReading>("/oracle/name", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  daily: (date?: string) =>
    request(`/oracle/daily${date ? `?date=${date}` : ""}`),
  suggestRange: (data: {
    scanned_ranges: string[];
    puzzle_number: number;
    ai_level: number;
  }) =>
    request("/oracle/suggest-range", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ─── Vault ───

export const vault = {
  findings: (params?: { limit?: number; offset?: number; chain?: string }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    if (params?.chain) query.set("chain", params.chain);
    return request<import("@/types").Finding[]>(`/vault/findings?${query}`);
  },
  summary: () => request<import("@/types").VaultSummary>("/vault/summary"),
  search: (q: string) =>
    request<import("@/types").Finding[]>(`/vault/search?q=${q}`),
  export: (format: "json" | "csv") =>
    request("/vault/export", {
      method: "POST",
      body: JSON.stringify({ format }),
    }),
};

// ─── Learning ───

export const learning = {
  stats: () => request<import("@/types").LearningStats>("/learning/stats"),
  insights: (limit?: number) =>
    request<import("@/types").Insight[]>(
      `/learning/insights?limit=${limit || 10}`,
    ),
  analyze: (data: { session_id: string }) =>
    request("/learning/analyze", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  weights: () =>
    request<{ weights: Record<string, number> }>("/learning/weights"),
  patterns: () => request("/learning/patterns"),
};
