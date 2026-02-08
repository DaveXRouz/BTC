// NPS V4 TypeScript types — mirrors API Pydantic models

// ─── Scanner ───

export interface PuzzleConfig {
  puzzle_number: number;
  range_start: string;
  range_end: string;
}

export interface ScanConfig {
  mode: "random_key" | "seed_phrase" | "both";
  chains: string[];
  batch_size: number;
  check_every_n: number;
  threads: number;
  checkpoint_interval: number;
  addresses_per_seed: number;
  score_threshold: number;
  puzzle?: PuzzleConfig;
}

export interface ScanSession {
  session_id: string;
  status: "running" | "paused" | "stopped";
  config: ScanConfig;
  started_at: string;
}

export interface ScanStats {
  session_id: string;
  keys_tested: number;
  seeds_tested: number;
  hits: number;
  keys_per_second: number;
  elapsed_seconds: number;
  checkpoint_count: number;
  current_mode: string;
  highest_score: number;
}

// ─── Oracle ───

export interface FC60Data {
  cycle: number;
  element: string;
  polarity: string;
  stem: string;
  branch: string;
  year_number: number;
  month_number: number;
  day_number: number;
  energy_level: number;
  element_balance: Record<string, number>;
}

export interface NumerologyData {
  life_path: number;
  day_vibration: number;
  personal_year: number;
  personal_month: number;
  personal_day: number;
  interpretation: string;
}

export interface OracleReading {
  fc60: FC60Data | null;
  numerology: NumerologyData | null;
  zodiac: Record<string, string> | null;
  chinese: Record<string, string> | null;
  summary: string;
  generated_at: string;
}

export interface QuestionResponse {
  question: string;
  answer: string;
  sign_number: number;
  interpretation: string;
  confidence: number;
}

export interface NameReading {
  name: string;
  destiny_number: number;
  soul_urge: number;
  personality: number;
  letters: { letter: string; value: number; element: string }[];
  interpretation: string;
}

// ─── Oracle Users ───

export interface OracleUser {
  id: number;
  name: string;
  name_persian?: string;
  birthday: string; // "YYYY-MM-DD"
  mother_name: string;
  mother_name_persian?: string;
  country?: string;
  city?: string;
  created_at?: string;
  updated_at?: string;
}

export interface OracleUserCreate {
  name: string;
  name_persian?: string;
  birthday: string;
  mother_name: string;
  mother_name_persian?: string;
  country?: string;
  city?: string;
}

export type OracleUserUpdate = Partial<OracleUserCreate>;

// ─── Vault ───

export interface Finding {
  id: string;
  address: string;
  chain: string;
  balance: number;
  score: number;
  source: string | null;
  puzzle_number: number | null;
  score_breakdown: Record<string, number> | null;
  metadata: Record<string, unknown>;
  found_at: string;
  session_id: string | null;
}

export interface VaultSummary {
  total: number;
  with_balance: number;
  by_chain: Record<string, number>;
  sessions: number;
}

// ─── Learning ───

export interface LearningStats {
  level: number;
  name: string;
  xp: number;
  xp_next: number | null;
  capabilities: string[];
}

export interface Insight {
  id: string | null;
  insight_type: "insight" | "recommendation";
  content: string;
  source: string | null;
  created_at: string | null;
}

// ─── WebSocket Events ───

export interface WSEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp?: number;
}

export type EventType =
  | "finding"
  | "health"
  | "ai_adjusted"
  | "level_up"
  | "checkpoint"
  | "terminal_status"
  | "scan_started"
  | "scan_stopped"
  | "high_score"
  | "config_changed"
  | "shutdown"
  | "stats_update"
  | "error";

// ─── Health ───

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  checks: Record<string, string>;
}

// ─── Auth ───

export interface User {
  id: string;
  username: string;
  role: string;
}

// ─── Currency (from V3 theme.py) ───

export const CURRENCY_SYMBOLS: Record<
  string,
  { symbol: string; color: string }
> = {
  BTC: { symbol: "\u20BF", color: "#F7931A" },
  ETH: { symbol: "\u039E", color: "#627EEA" },
  USDT: { symbol: "\u20AE", color: "#26A17B" },
  USDC: { symbol: "\u25C9", color: "#2775CA" },
  DAI: { symbol: "\u25C8", color: "#F5AC37" },
  WBTC: { symbol: "\u20BFw", color: "#F09242" },
  LINK: { symbol: "\u2B21", color: "#2A5ADA" },
  SHIB: { symbol: "SHIB", color: "#FFA409" },
};
