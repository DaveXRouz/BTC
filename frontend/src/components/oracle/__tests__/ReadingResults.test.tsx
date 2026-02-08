import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { ReadingResults } from "../ReadingResults";
import type { ConsultationResult } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.tab_summary": "Summary",
        "oracle.tab_details": "Details",
        "oracle.tab_history": "History",
        "oracle.results_placeholder":
          "Results will appear here after a reading.",
        "oracle.details_placeholder":
          "Submit a reading to see detailed analysis.",
        "oracle.type_reading": "Reading",
        "oracle.element": "Element",
        "oracle.energy": "Energy",
        "oracle.life_path": "Life Path",
        "oracle.generated_at": "Generated at",
        "oracle.details_fc60": "FC60 Analysis",
        "oracle.details_numerology": "Numerology",
        "oracle.cycle": "Cycle",
        "oracle.polarity": "Polarity",
        "oracle.stem": "Stem",
        "oracle.branch": "Branch",
        "oracle.element_balance": "Element Balance",
        "oracle.day_vibration": "Day Vibration",
        "oracle.personal_year": "Personal Year",
        "oracle.personal_month": "Personal Month",
        "oracle.personal_day": "Personal Day",
        "oracle.filter_all": "All",
        "oracle.filter_reading": "Readings",
        "oracle.filter_question": "Questions",
        "oracle.filter_name": "Names",
        "oracle.history_empty": "No readings yet.",
        "oracle.error_history": "Failed to load reading history.",
        "oracle.export_text": "Export TXT",
        "oracle.export_json": "Export JSON",
        "oracle.translate": "Translate to Persian",
        "common.loading": "Loading...",
      };
      return map[key] ?? key;
    },
  }),
}));

vi.mock("@/services/api", () => ({
  oracle: {
    history: vi.fn().mockReturnValue(new Promise(() => {})),
  },
  translation: { translate: vi.fn() },
}));

const readingResult: ConsultationResult = {
  type: "reading",
  data: {
    fc60: {
      cycle: 1,
      element: "Wood",
      polarity: "Yang",
      stem: "Jia",
      branch: "Zi",
      year_number: 1,
      month_number: 2,
      day_number: 3,
      energy_level: 7,
      element_balance: { Wood: 3 },
    },
    numerology: {
      life_path: 5,
      day_vibration: 3,
      personal_year: 1,
      personal_month: 4,
      personal_day: 7,
      interpretation: "New beginnings",
    },
    zodiac: null,
    chinese: null,
    moon: null,
    angel: null,
    chaldean: null,
    ganzhi: null,
    fc60_extended: null,
    synchronicities: [],
    ai_interpretation: null,
    summary: "Test summary for reading",
    generated_at: "2024-01-01T12:00:00Z",
  },
};

describe("ReadingResults", () => {
  it("renders all three tabs", () => {
    renderWithProviders(<ReadingResults result={null} />);
    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText("Details")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("shows placeholder on summary tab by default", () => {
    renderWithProviders(<ReadingResults result={null} />);
    expect(
      screen.getByText("Results will appear here after a reading."),
    ).toBeInTheDocument();
  });

  it("switches to details tab on click", async () => {
    renderWithProviders(<ReadingResults result={null} />);
    await userEvent.click(screen.getByText("Details"));
    expect(
      screen.getByText("Submit a reading to see detailed analysis."),
    ).toBeInTheDocument();
  });

  it("shows result on summary tab", () => {
    renderWithProviders(<ReadingResults result={readingResult} />);
    expect(screen.getByText("Test summary for reading")).toBeInTheDocument();
    expect(screen.getByText("Reading")).toBeInTheDocument();
  });

  it("shows export buttons when result exists", () => {
    renderWithProviders(<ReadingResults result={readingResult} />);
    expect(screen.getByText("Export TXT")).toBeInTheDocument();
    expect(screen.getByText("Export JSON")).toBeInTheDocument();
  });

  it("does not show export buttons when no result", () => {
    renderWithProviders(<ReadingResults result={null} />);
    expect(screen.queryByText("Export TXT")).not.toBeInTheDocument();
    expect(screen.queryByText("Export JSON")).not.toBeInTheDocument();
  });
});
