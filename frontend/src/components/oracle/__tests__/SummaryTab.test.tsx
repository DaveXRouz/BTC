import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SummaryTab } from "../SummaryTab";
import type { ConsultationResult } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.results_placeholder":
          "Results will appear here after a reading.",
        "oracle.type_reading": "Reading",
        "oracle.type_question": "Question",
        "oracle.type_name": "Name",
        "oracle.element": "Element",
        "oracle.energy": "Energy",
        "oracle.life_path": "Life Path",
        "oracle.answer": "Answer",
        "oracle.confidence": "Confidence",
        "oracle.generated_at": "Generated at",
        "oracle.translate": "Translate to Persian",
      };
      return map[key] ?? key;
    },
  }),
}));

vi.mock("@/services/api", () => ({
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
      element_balance: { Wood: 3, Fire: 1 },
    },
    numerology: {
      life_path: 5,
      day_vibration: 3,
      personal_year: 1,
      personal_month: 4,
      personal_day: 7,
      interpretation: "A year of new beginnings",
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
    summary: "This is a test reading summary",
    generated_at: "2024-01-01T12:00:00Z",
  },
};

const questionResult: ConsultationResult = {
  type: "question",
  data: {
    question: "Will it work?",
    answer: "Yes",
    sign_number: 42,
    interpretation: "Signs point to yes",
    confidence: 0.85,
  },
};

describe("SummaryTab", () => {
  it("shows placeholder when no result", () => {
    render(<SummaryTab result={null} />);
    expect(
      screen.getByText("Results will appear here after a reading."),
    ).toBeInTheDocument();
  });

  it("shows type badge for reading", () => {
    render(<SummaryTab result={readingResult} />);
    expect(screen.getByText("Reading")).toBeInTheDocument();
  });

  it("shows summary text for reading", () => {
    render(<SummaryTab result={readingResult} />);
    expect(
      screen.getByText("This is a test reading summary"),
    ).toBeInTheDocument();
  });

  it("shows quick stats for reading", () => {
    render(<SummaryTab result={readingResult} />);
    expect(screen.getByText("Wood")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows answer and confidence for question", () => {
    render(<SummaryTab result={questionResult} />);
    expect(screen.getByText("Question")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
  });
});
