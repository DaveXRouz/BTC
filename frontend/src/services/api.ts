/**
 * NPS API client — typed fetch wrappers for all endpoints.
 */

const API_BASE = "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }
  get isServerError(): boolean {
    return this.status >= 500;
  }
  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

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

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch {
    throw new ApiError("Network error", 0);
  }

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    const detail = body.detail || `HTTP ${response.status}`;
    throw new ApiError(detail, response.status, detail);
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

// ─── Dashboard ───

export const dashboard = {
  stats: () => request<import("@/types").DashboardStats>("/oracle/stats"),
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

// ─── Share ───

export const share = {
  create: (readingId: number, expiresInDays?: number) =>
    request<import("@/types").ShareLink>("/share", {
      method: "POST",
      body: JSON.stringify({
        reading_id: readingId,
        expires_in_days: expiresInDays,
      }),
    }),
  get: (token: string) =>
    request<import("@/types").SharedReadingData>(`/share/${token}`),
  revoke: (token: string) =>
    request<void>(`/share/${token}`, { method: "DELETE" }),
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
  feedback: {
    submit: (readingId: number, data: import("@/types").FeedbackRequest) =>
      request<import("@/types").FeedbackResponse>(
        `/learning/oracle/readings/${readingId}/feedback`,
        {
          method: "POST",
          body: JSON.stringify(data),
        },
      ),
    get: (readingId: number) =>
      request<import("@/types").FeedbackResponse[]>(
        `/learning/oracle/readings/${readingId}/feedback`,
      ),
  },
  learningStats: {
    get: () =>
      request<import("@/types").OracleLearningStats>("/learning/oracle/stats"),
    recalculate: () =>
      request<import("@/types").OracleLearningStats>(
        "/learning/oracle/recalculate",
        { method: "POST" },
      ),
  },
};

// ─── Admin ───

export const admin = {
  listUsers: (params?: {
    limit?: number;
    offset?: number;
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset !== undefined)
      query.set("offset", String(params.offset));
    if (params?.search) query.set("search", params.search);
    if (params?.sort_by) query.set("sort_by", params.sort_by);
    if (params?.sort_order) query.set("sort_order", params.sort_order);
    return request<import("@/types").SystemUserListResponse>(
      `/admin/users?${query}`,
    );
  },
  getUser: (id: string) =>
    request<import("@/types").SystemUser>(`/admin/users/${id}`),
  updateRole: (id: string, role: string) =>
    request<import("@/types").SystemUser>(`/admin/users/${id}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),
  resetPassword: (id: string) =>
    request<import("@/types").PasswordResetResult>(
      `/admin/users/${id}/reset-password`,
      { method: "POST" },
    ),
  updateStatus: (id: string, is_active: boolean) =>
    request<import("@/types").SystemUser>(`/admin/users/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active }),
    }),
  stats: () => request<import("@/types").AdminStats>("/admin/stats"),
  listProfiles: (params?: {
    limit?: number;
    offset?: number;
    search?: string;
    sort_by?: string;
    sort_order?: string;
    include_deleted?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset !== undefined)
      query.set("offset", String(params.offset));
    if (params?.search) query.set("search", params.search);
    if (params?.sort_by) query.set("sort_by", params.sort_by);
    if (params?.sort_order) query.set("sort_order", params.sort_order);
    if (params?.include_deleted)
      query.set("include_deleted", String(params.include_deleted));
    return request<import("@/types").AdminOracleProfileListResponse>(
      `/admin/profiles?${query}`,
    );
  },
  deleteProfile: (id: number) =>
    request<void>(`/admin/profiles/${id}`, { method: "DELETE" }),
};
