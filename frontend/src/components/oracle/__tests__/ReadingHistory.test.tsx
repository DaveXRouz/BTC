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
        "oracle.filter_reading": "Readings",
        "oracle.filter_question": "Questions",
        "oracle.filter_name": "Names",
        "oracle.history_empty": "No readings yet.",
        "oracle.history_count": `${params?.count ?? 0} readings`,
        "oracle.load_more": "Load More",
        "oracle.error_history": "Failed to load reading history.",
        "common.loading": "Loading...",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockHistory = vi.fn();

vi.mock("@/services/api", () => ({
  oracle: {
    history: (...args: unknown[]) => mockHistory(...args),
  },
}));

beforeEach(() => {
  mockHistory.mockReset();
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
      limit: 20,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("No readings yet.")).toBeInTheDocument();
    });
  });

  it("renders filter chips", () => {
    mockHistory.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<ReadingHistory />);
    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("Readings")).toBeInTheDocument();
    expect(screen.getByText("Questions")).toBeInTheDocument();
    expect(screen.getByText("Names")).toBeInTheDocument();
  });

  it("renders history items", async () => {
    mockHistory.mockResolvedValue({
      readings: [
        {
          id: 1,
          user_id: null,
          sign_type: "reading",
          sign_value: "test-sign",
          question: null,
          reading_result: { foo: "bar" },
          ai_interpretation: "Test interpretation",
          created_at: "2024-01-01T12:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("test-sign")).toBeInTheDocument();
    });
    expect(screen.getByText("1 readings")).toBeInTheDocument();
  });

  it("expands history item on click", async () => {
    mockHistory.mockResolvedValue({
      readings: [
        {
          id: 1,
          user_id: null,
          sign_type: "reading",
          sign_value: "test-sign",
          question: null,
          reading_result: null,
          ai_interpretation: "Detailed interpretation text",
          created_at: "2024-01-01T12:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("test-sign")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("test-sign"));
    expect(
      screen.getByText("Detailed interpretation text"),
    ).toBeInTheDocument();
  });

  it("shows load more when more items available", async () => {
    mockHistory.mockResolvedValue({
      readings: Array.from({ length: 20 }, (_, i) => ({
        id: i + 1,
        user_id: null,
        sign_type: "reading",
        sign_value: `sign-${i}`,
        question: null,
        reading_result: null,
        ai_interpretation: null,
        created_at: "2024-01-01T12:00:00Z",
      })),
      total: 30,
      limit: 20,
      offset: 0,
    });
    renderWithProviders(<ReadingHistory />);
    await waitFor(() => {
      expect(screen.getByText("Load More")).toBeInTheDocument();
    });
  });
});
