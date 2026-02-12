/**
 * NPS API client — typed fetch wrappers for all endpoints.
 */

const API_BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Auth token: JWT from localStorage or fallback to API key from env
  const token =
    localStorage.getItem("nps_token") || import.meta.env.VITE_API_KEY;
  if (token) headers["Authorization"] = `Bearer ${token}`;

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
  question: (question: string, userId?: number, system?: string) =>
    request<import("@/types").QuestionReadingResult>("/oracle/question", {
      method: "POST",
      body: JSON.stringify({
        question,
        user_id: userId,
        numerology_system: system || "auto",
        include_ai: true,
      }),
    }),
  name: (name: string, userId?: number, system?: string) =>
    request<import("@/types").NameReading>("/oracle/name", {
      method: "POST",
      body: JSON.stringify({
        name,
        user_id: userId,
        numerology_system: system || "pythagorean",
        include_ai: true,
      }),
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
  history: (params?: import("@/types").ReadingSearchParams) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset !== undefined)
      query.set("offset", String(params.offset));
    if (params?.sign_type) query.set("sign_type", params.sign_type);
    if (params?.search) query.set("search", params.search);
    if (params?.date_from) query.set("date_from", params.date_from);
    if (params?.date_to) query.set("date_to", params.date_to);
    if (params?.is_favorite !== undefined)
      query.set("is_favorite", String(params.is_favorite));
    return request<import("@/types").StoredReadingListResponse>(
      `/oracle/readings?${query}`,
    );
  },
  getReading: (id: number) =>
    request<import("@/types").StoredReading>(`/oracle/readings/${id}`),
  deleteReading: (id: number) =>
    request<void>(`/oracle/readings/${id}`, { method: "DELETE" }),
  toggleFavorite: (id: number) =>
    request<import("@/types").StoredReading>(
      `/oracle/readings/${id}/favorite`,
      { method: "PATCH" },
    ),
  readingStats: () =>
    request<import("@/types").ReadingStats>("/oracle/readings/stats"),
  validateStamp: (stamp: string) =>
    request<import("@/types").StampValidateResponse>("/oracle/validate-stamp", {
      method: "POST",
      body: JSON.stringify({ stamp }),
    }),
  timeReading: (data: import("@/types").TimeReadingRequest) =>
    request<import("@/types").FrameworkReadingResponse>("/oracle/readings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  dailyReading: (data: import("@/types").DailyReadingRequest) =>
    request<import("@/types").FrameworkReadingResponse>("/oracle/readings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getDailyReading: (userId: number, date?: string) =>
    request<import("@/types").DailyReadingCacheResponse>(
      `/oracle/daily/reading?user_id=${userId}${date ? `&date=${date}` : ""}`,
    ),
  multiUserFrameworkReading: (
    data: import("@/types").MultiUserFrameworkRequest,
  ) =>
    request<import("@/types").MultiUserFrameworkResponse>("/oracle/readings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ─── Oracle Users ───

export const oracleUsers = {
  list: async (): Promise<import("@/types").OracleUser[]> => {
    const resp = await request<{
      users: import("@/types").OracleUser[];
      total: number;
      limit: number;
      offset: number;
    }>("/oracle/users");
    return resp.users;
  },
  get: (id: number) =>
    request<import("@/types").OracleUser>(`/oracle/users/${id}`),
  create: (data: import("@/types").OracleUserCreate) =>
    request<import("@/types").OracleUser>("/oracle/users", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: import("@/types").OracleUserUpdate) =>
    request<import("@/types").OracleUser>(`/oracle/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    request<void>(`/oracle/users/${id}`, { method: "DELETE" }),
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

// ─── Translation ───

export const translation = {
  translate: (text: string, sourceLang = "en", targetLang = "fa") =>
    request<import("@/types").TranslateResponse>("/translation/translate", {
      method: "POST",
      body: JSON.stringify({
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
      }),
    }),
  detect: (text: string) =>
    request<import("@/types").DetectResponse>(
      `/translation/detect?text=${encodeURIComponent(text)}`,
    ),
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
