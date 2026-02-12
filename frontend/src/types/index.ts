// NPS TypeScript types — mirrors API Pydantic models

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

export interface MoonData {
  phase_name: string;
  illumination: number;
  age_days: number;
  meaning: string;
  emoji: string;
}

export interface AngelMatch {
  number: number;
  meaning: string;
}

export interface AngelData {
  matches: AngelMatch[];
}

export interface ChaldeanData {
  value: number;
  meaning: string;
  letter_values: string;
}

export interface GanzhiData {
  year_name: string;
  year_animal: string;
  stem_element: string;
  stem_polarity: string;
  hour_animal: string;
  hour_branch: string;
}

export interface FC60Extended {
  stamp: string;
  weekday_name: string;
  weekday_planet: string;
  weekday_domain: string;
}

export interface OracleReading {
  fc60: FC60Data | null;
  numerology: NumerologyData | null;
  zodiac: Record<string, string> | null;
  chinese: Record<string, string> | null;
  moon: MoonData | null;
  angel: AngelData | null;
  chaldean: ChaldeanData | null;
  ganzhi: GanzhiData | null;
  fc60_extended: FC60Extended | null;
  synchronicities: string[];
  ai_interpretation: string | null;
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

export interface NameReadingRequest {
  name: string;
  user_id?: number;
  numerology_system?: string;
  include_ai?: boolean;
}

export interface NameReading {
  name: string;
  detected_script: string;
  numerology_system: string;
  expression: number;
  soul_urge: number;
  personality: number;
  life_path: number | null;
  personal_year: number | null;
  fc60_stamp: Record<string, unknown> | null;
  moon: Record<string, unknown> | null;
  ganzhi: Record<string, unknown> | null;
  patterns: Record<string, unknown> | null;
  confidence: { score: number; level: string; factors?: string } | null;
  ai_interpretation: string | null;
  letter_breakdown: { letter: string; value: number; element: string }[];
  reading_id: number | null;
}

export interface QuestionReadingRequest {
  question: string;
  user_id?: number;
  numerology_system?: string;
  include_ai?: boolean;
}

export interface QuestionReadingResult {
  question: string;
  question_number: number;
  detected_script: string;
  numerology_system: string;
  raw_letter_sum: number;
  is_master_number: boolean;
  fc60_stamp: Record<string, unknown> | null;
  numerology: Record<string, unknown> | null;
  moon: Record<string, unknown> | null;
  ganzhi: Record<string, unknown> | null;
  patterns: Record<string, unknown> | null;
  confidence: { score: number; level: string; factors?: string } | null;
  ai_interpretation: string | null;
  reading_id: number | null;
}

// ─── Oracle Results ───

// Union of all reading results from API
export type ConsultationResult =
  | { type: "reading"; data: OracleReading }
  | { type: "question"; data: QuestionReadingResult }
  | { type: "name"; data: NameReading };

// Stored reading from GET /oracle/readings — mirrors backend StoredReadingResponse
export interface StoredReading {
  id: number;
  user_id: number | null;
  sign_type: string;
  sign_value: string;
  question: string | null;
  reading_result: Record<string, unknown> | null;
  ai_interpretation: string | null;
  created_at: string;
  is_favorite: boolean;
  deleted_at: string | null;
}

// Paginated response — mirrors backend StoredReadingListResponse
export interface StoredReadingListResponse {
  readings: StoredReading[];
  total: number;
  limit: number;
  offset: number;
}

// Reading search/filter params
export interface ReadingSearchParams {
  limit?: number;
  offset?: number;
  sign_type?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  is_favorite?: boolean;
}

// Reading statistics — mirrors backend ReadingStatsResponse
export interface ReadingStats {
  total_readings: number;
  by_type: Record<string, number>;
  by_month: { month: string; count: number }[];
  favorites_count: number;
  most_active_day: string | null;
}

export type ResultsTab = "summary" | "details" | "history";

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
  gender?: string; // "male" | "female" | null
  heart_rate_bpm?: number; // 30-220 | null
  timezone_hours?: number; // -12 to +14
  timezone_minutes?: number; // 0-59
  latitude?: number; // -90 to 90
  longitude?: number; // -180 to 180
  created_by?: string; // UUID of system user who created this profile
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
  gender?: string;
  heart_rate_bpm?: number;
  timezone_hours?: number;
  timezone_minutes?: number;
  latitude?: number;
  longitude?: number;
}

export type OracleUserUpdate = Partial<OracleUserCreate>;

// ─── Oracle Consultation ───

export type SignType = "time" | "number" | "carplate" | "custom";

export interface SignData {
  type: SignType;
  value: string;
}

export interface LocationData {
  lat: number;
  lon: number;
  country?: string;
  countryCode?: string;
  city?: string;
  timezone?: string;
}

export interface OracleConsultationData {
  userId: number;
  question: string;
  sign: SignData;
  location: LocationData | null;
}

// ─── Multi-User Oracle ───

export interface SelectedUsers {
  primary: OracleUser;
  secondary: OracleUser[];
}

export interface MultiUserInput {
  name: string;
  birth_year: number;
  birth_month: number;
  birth_day: number;
  user_id?: number;
}

export interface MultiUserReadingRequest {
  users: MultiUserInput[];
  primary_user_index: number;
  include_interpretation: boolean;
}

export interface CompatibilityScore {
  user1: string;
  user2: string;
  overall: number;
  classification: string;
  scores: Record<string, number>;
  strengths: string[];
  challenges: string[];
}

export interface GroupEnergy {
  dominant_element: string;
  dominant_animal: string;
  joint_life_path: number;
  archetype: string;
  archetype_description: string;
  element_distribution: Record<string, number>;
  animal_distribution: Record<string, number>;
  life_path_distribution: Record<string, number>;
}

export interface GroupDynamics {
  avg_compatibility: number;
  strongest_bond: Record<string, unknown>;
  weakest_bond: Record<string, unknown>;
  roles: Record<string, Record<string, unknown>>;
  synergies: string[];
  challenges: string[];
  growth_areas: string[];
}

export interface UserProfile {
  name: string;
  element: string;
  animal: string;
  polarity: string;
  life_path: number;
  destiny_number: number;
  stem: string;
  branch: string;
  birth_year: number;
  birth_month: number;
  birth_day: number;
  fc60_sign: string;
  name_energy: number;
}

export interface MultiUserReadingResponse {
  user_count: number;
  pair_count: number;
  computation_ms: number;
  profiles: UserProfile[];
  pairwise_compatibility: CompatibilityScore[];
  group_energy: GroupEnergy | null;
  group_dynamics: GroupDynamics | null;
  ai_interpretation: Record<string, unknown> | null;
  reading_id: number | null;
}

// ─── FC60 Stamp (Framework-aligned, Session 10) ───

export interface FC60StampSegment {
  token: string;
  value?: number;
  animalName?: string;
  elementName?: string;
}

export interface FC60StampWeekday {
  token: string;
  name: string;
  planet: string;
  domain: string;
}

export interface FC60StampTime {
  half: string; // "☀" or "🌙"
  hour: FC60StampSegment;
  minute: FC60StampSegment;
  second: FC60StampSegment;
}

export interface FC60StampData {
  fc60: string;
  j60: string;
  y60: string;
  chk: string;
  weekday: FC60StampWeekday;
  month: FC60StampSegment & { index: number };
  dom: FC60StampSegment;
  time: FC60StampTime | null;
}

export interface StampValidateResponse {
  valid: boolean;
  stamp: string;
  decoded: Record<string, unknown> | null;
  error: string | null;
}

// ─── Cosmic Cycles (Session 11) ───

export interface MoonPhaseData {
  phase_name: string;
  emoji: string;
  age: number;
  illumination: number;
  energy: string;
  best_for: string;
  avoid: string;
}

export interface GanzhiCycleData {
  animal_name: string;
  element: string;
  polarity: string;
  gz_token: string;
  traditional_name?: string;
}

export interface GanzhiFullData {
  year: GanzhiCycleData;
  day: GanzhiCycleData;
  hour?: {
    animal_name: string;
  };
}

export interface CurrentMomentData {
  weekday: string;
  planet: string;
  domain: string;
}

export interface PlanetMoonCombo {
  theme: string;
  message: string;
}

export interface CosmicCycleData {
  moon: MoonPhaseData | null;
  ganzhi: GanzhiFullData | null;
  current: CurrentMomentData | null;
  planet_moon: PlanetMoonCombo | null;
}

// ─── Heartbeat & Location (Session 12) ───

export interface HeartbeatData {
  bpm: number;
  bpm_source: "actual" | "estimated";
  element: string;
  beats_per_day: number;
  total_lifetime_beats: number;
  rhythm_token: string;
}

export interface LocationElementData {
  element: string;
  timezone_estimate: number;
  lat_hemisphere: "N" | "S";
  lon_hemisphere: "E" | "W";
  lat_polarity: "Yang" | "Yin";
  lon_polarity: "Yang" | "Yin";
}

export interface ConfidenceData {
  score: number;
  level: "low" | "medium" | "high" | "very_high";
  factors: string;
}

export interface ConfidenceBoost {
  field: string;
  label: string;
  boost: number;
  filled: boolean;
}

// ─── Framework Reading (Session 14+) ───

export interface TimeReadingRequest {
  user_id: number;
  reading_type: "time";
  sign_value: string; // "HH:MM:SS"
  date?: string; // "YYYY-MM-DD"
  locale?: string; // "en" | "fa"
  numerology_system?: string; // "pythagorean" | "chaldean" | "abjad" | "auto"
}

export interface FrameworkConfidence {
  score: number;
  level: string;
  factors?: string;
}

export interface PatternDetected {
  type: string;
  strength: string;
  message?: string;
  animal?: string;
  number?: number;
  occurrences?: number;
}

export interface AIInterpretationSections {
  header: string;
  universal_address: string;
  core_identity: string;
  right_now: string;
  patterns: string;
  message: string;
  advice: string;
  caution: string;
  footer: string;
  full_text: string;
  ai_generated: boolean;
  locale: string;
  elapsed_ms: number;
  cached: boolean;
  confidence_score: number;
}

export interface FrameworkNumerologyData {
  life_path: { number: number; title: string; message: string } | null;
  expression: number;
  soul_urge: number;
  personality: number;
  personal_year: number;
  personal_month: number;
  personal_day: number;
  gender_polarity?: {
    gender: string;
    polarity: number;
    label: string;
  } | null;
  mother_influence?: number | null;
}

export interface FrameworkReadingResponse {
  id: number;
  reading_type: string;
  sign_value: string;
  framework_result: Record<string, unknown>;
  ai_interpretation: AIInterpretationSections | null;
  confidence: FrameworkConfidence;
  patterns: PatternDetected[];
  fc60_stamp: string;
  numerology: FrameworkNumerologyData | null;
  moon: Record<string, unknown> | null;
  ganzhi: Record<string, unknown> | null;
  locale: string;
  created_at: string;
}

export interface ReadingProgressEvent {
  step: number;
  total: number;
  message: string;
  reading_type: string;
}

// ─── Daily Reading (Session 16) ───

export interface DailyReadingRequest {
  user_id: number;
  reading_type: "daily";
  date?: string;
  locale?: string;
  numerology_system?: string;
  force_regenerate?: boolean;
}

export interface DailyInsights {
  suggested_activities: string[];
  energy_forecast: string;
  lucky_hours: number[];
  focus_area: string;
  element_of_day: string;
}

export interface DailyReadingCacheResponse {
  user_id: number;
  date: string;
  reading:
    | (FrameworkReadingResponse & { daily_insights?: DailyInsights })
    | null;
  cached: boolean;
  generated_at: string | null;
}

// ─── Multi-User Framework Reading (Session 16) ───

export interface MultiUserFrameworkRequest {
  user_ids: number[];
  primary_user_index: number;
  reading_type: "multi";
  date?: string;
  locale?: string;
  numerology_system?: string;
  include_interpretation?: boolean;
}

export interface PairwiseCompatibilityResult {
  user_a_name: string;
  user_b_name: string;
  user_a_id: number;
  user_b_id: number;
  overall_score: number;
  overall_percentage: number;
  classification: string;
  dimensions: Record<string, number>;
  strengths: string[];
  challenges: string[];
  description: string;
}

export interface GroupAnalysisResult {
  group_harmony_score: number;
  group_harmony_percentage: number;
  element_balance: Record<string, number>;
  animal_distribution: Record<string, number>;
  dominant_element: string;
  dominant_animal: string;
  group_summary: string;
}

export interface MultiUserFrameworkResponse {
  id: number | null;
  user_count: number;
  pair_count: number;
  computation_ms: number;
  individual_readings: FrameworkReadingResponse[];
  pairwise_compatibility: PairwiseCompatibilityResult[];
  group_analysis: GroupAnalysisResult | null;
  ai_interpretation: AIInterpretationSections | null;
  locale: string;
  created_at: string;
}

// ─── Translation ───

export interface TranslateResponse {
  source_text: string;
  translated_text: string;
  source_lang: string;
  target_lang: string;
  preserved_terms: string[];
  ai_generated: boolean;
  elapsed_ms: number;
  cached: boolean;
}

export interface DetectResponse {
  text: string;
  detected_lang: string;
  confidence: number;
}

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

// ─── Oracle Feedback & Learning (Session 18) ───

export interface SectionFeedback {
  section: string;
  helpful: boolean;
}

export interface FeedbackRequest {
  rating: number;
  section_feedback: SectionFeedback[];
  text_feedback?: string;
}

export interface FeedbackResponse {
  id: number;
  reading_id: number;
  rating: number;
  section_feedback: Record<string, string>;
  text_feedback: string | null;
  created_at: string;
  updated: boolean;
}

export interface OracleLearningStats {
  total_feedback_count: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
  avg_by_reading_type: Record<string, number>;
  avg_by_format: Record<string, number>;
  section_helpful_pct: Record<string, number>;
  active_prompt_adjustments: string[];
  last_recalculated: string | null;
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
  | "reading_progress"
  | "error";

// ─── Oracle Reading Types ───

export type ReadingType = "time" | "name" | "question" | "daily" | "multi";

// ─── Dashboard ───

export interface DashboardStats {
  total_readings: number;
  readings_by_type: Record<string, number>;
  average_confidence: number | null;
  most_used_type: string | null;
  streak_days: number;
  readings_today: number;
  readings_this_week: number;
  readings_this_month: number;
}

export interface MoonPhaseInfo {
  phase_name: string;
  illumination: number;
  emoji: string;
  age_days: number;
}

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

// ─── Currency (from legacy theme.py) ───

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
