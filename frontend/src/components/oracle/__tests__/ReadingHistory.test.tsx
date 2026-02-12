import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { ReadingHistory } from "../ReadingHistory";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const map: Record<string, string> = {
        "oracle.filter_all": "All",
        "oracle.filter_time": "Time",
        "oracle.filter_reading": "Readings",
        "oracle.filter_question": "Questions",
        "oracle.filter_name": "Names",
        "oracle.filter_daily": "Daily",
        "oracle.filter_multi": "Multi-User",
        "oracle.filter_favorites": "Favorites only",
        "oracle.history_empty": "No readings yet.",
        "oracle.history_count": `${params?.count ?? 0} readings`,
        "oracle.load_more": "Load More",
        "oracle.error_history": "Failed to load reading history.",
        "oracle.search_placeholder": "Search readings...",
        "oracle.date_to_label": "to",
        "oracle.toggle_favorite": "Toggle favorite",
        "oracle.delete_reading": "Delete",
        "oracle.stats_total": `${params?.count ?? 0} total`,
        "oracle.stats_favorites": `${params?.count ?? 0} favorites`,
        "oracle.page_indicator": `${params?.current ?? 1} / ${params?.total ?? 1}`,
        "common.loading": "Loading...",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockHistory = vi.fn();
const mockDeleteReading = vi.fn();
const mockToggleFavorite = vi.fn();
const mockReadingStats = vi.fn();

vi.mock("@/services/api", () => ({
  oracle: {
    history: (...args: unknown[]) => mockHistory(...args),
    deleteReading: (...args: unknown[]) => mockDeleteReading(...args),
    toggleFavorite: (...args: unknown[]) => mockToggleFavorite(...args),
    readingStats: (...args: unknown[]) => mockReadingStats(...args),
  },
}));

const sampleReading = {
  id: 1,
  user_id: null,
  sign_type: "reading",
  sign_value: "test-sign",
  question: null,
  reading_result: { foo: "bar" },
  ai_interpretation: "Test interpretation",
  created_at: "2024-01-01T12:00:00Z",
  is_favorite: false,
  deleted_at: null,
};

beforeEach(() => {
  mockHistory.mockReset();
  mockDeleteReading.mockReset();
  mockToggleFavorite.mockReset();
  mockReadingStats.mockReset();
  mockReadingStats.mockResolvedValue({
    total_readings: 0,
    by_type: {},
    by_month: [],
    favorites_count: 0,
    most_active_day: null,
  });
});

describe("ReadingHistory", () => {
  it("shows loading state", () => {
    mockHistory.mockReturnValue(new Promise(() => {})); // never resolves
    renderWithProviders(<ReadingHistory />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows empty state when no readings", async () => {
    mockHistory.mockResolvedValue({
      readings: [],
      total: 0,
      limit: 12,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("No readings yet.")).toBeInTheDocument();
    });
  });

  it("renders filter chips including new types", () => {
    mockHistory.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<ReadingHistory />);
    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("Time")).toBeInTheDocument();
    expect(screen.getByText("Questions")).toBeInTheDocument();
    expect(screen.getByText("Names")).toBeInTheDocument();
    expect(screen.getByText("Daily")).toBeInTheDocument();
    expect(screen.getByText("Multi-User")).toBeInTheDocument();
  });

  it("renders history items as cards", async () => {
    mockHistory.mockResolvedValue({
      readings: [sampleReading],
      total: 1,
      limit: 12,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("test-sign")).toBeInTheDocument();
    });
    expect(screen.getByText("1 readings")).toBeInTheDocument();
  });

  it("renders search input", () => {
    mockHistory.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<ReadingHistory />);
    expect(
      screen.getByPlaceholderText("Search readings..."),
    ).toBeInTheDocument();
  });

  it("renders date range inputs", () => {
    mockHistory.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<ReadingHistory />);
    expect(screen.getByText("to")).toBeInTheDocument();
  });

  it("renders favorites toggle button", () => {
    mockHistory.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<ReadingHistory />);
    expect(screen.getByTitle("Favorites only")).toBeInTheDocument();
  });

  it("shows pagination when multiple pages", async () => {
    mockHistory.mockResolvedValue({
      readings: Array.from({ length: 12 }, (_, i) => ({
        ...sampleReading,
        id: i + 1,
        sign_value: `sign-${i}`,
      })),
      total: 30,
      limit: 12,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("1 / 3")).toBeInTheDocument();
    });
  });

  it("changes filter when chip is clicked", async () => {
    mockHistory.mockResolvedValue({
      readings: [],
      total: 0,
      limit: 12,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("No readings yet.")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("Questions"));
    // After click, mockHistory should have been called again with sign_type
    await waitFor(() => {
      expect(mockHistory).toHaveBeenCalledWith(
        expect.objectContaining({ sign_type: "question" }),
      );
    });
  });

  it("shows star icons on reading cards", async () => {
    const favReading = { ...sampleReading, is_favorite: true };
    mockHistory.mockResolvedValue({
      readings: [favReading],
      total: 1,
      limit: 12,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByTitle("Toggle favorite")).toBeInTheDocument();
    });
    // Filled star for favorite
    expect(screen.getByTitle("Toggle favorite").textContent).toBe("\u2605");
  });

  it("shows stats when available", async () => {
    mockReadingStats.mockResolvedValue({
      total_readings: 42,
      by_type: { reading: 20, question: 22 },
      by_month: [],
      favorites_count: 5,
      most_active_day: null,
    });
    mockHistory.mockResolvedValue({
      readings: [],
      total: 0,
      limit: 12,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("42 total")).toBeInTheDocument();
      expect(screen.getByText("5 favorites")).toBeInTheDocument();
    });
  });
});
