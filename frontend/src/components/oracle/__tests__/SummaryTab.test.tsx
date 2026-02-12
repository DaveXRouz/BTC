import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SummaryTab } from "../SummaryTab";
import type { ConsultationResult } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      const map: Record<string, string> = {
        "oracle.results_placeholder":
          "Results will appear here after a reading.",
        "oracle.type_reading": "Reading",
        "oracle.type_question": "Question",
        "oracle.type_name": "Name",
        "oracle.element": "Element",
        "oracle.energy": "Energy",
        "oracle.life_path": "Life Path",
        "oracle.day_vibration": "Day Vibration",
        "oracle.personal_year": "Personal Year",
        "oracle.question_number_label": "Question Number",
        "oracle.detected_script": `Detected: ${opts?.script ?? ""}`,
        "oracle.confidence": "Confidence",
        "oracle.generated_at": "Generated at",
        "oracle.translate": "Translate to Persian",
        "oracle.current_reading": "Current Reading",
        "oracle.section_universal_address": "Universal Address",
        "oracle.section_core_identity": "Core Identity",
        "oracle.section_right_now": "Right Now",
        "oracle.section_patterns": "Patterns & Synchronicities",
        "oracle.section_message": "The Message",
        "oracle.section_advice": "Today's Advice",
        "oracle.section_caution": "Caution",
        "oracle.no_patterns": "No synchronicities detected",
        "oracle.confidence_label": "Reading Confidence",
        "oracle.powered_by": "Powered by NPS Numerology Framework",
        "oracle.disclaimer": "This reading is for entertainment purposes only.",
        "oracle.expression": "Expression",
        "oracle.soul_urge": "Soul Urge",
        "oracle.personality": "Personality",
        "oracle.details_letters": "Letter Analysis",
        "oracle.master_number_badge": "Master Number",
        "oracle.caution_missing": "missing from chart",
        "oracle.caution_dominant": "dominant in chart",
        "oracle.numerology_system": "System",
      };
      return map[key] ?? key;
    },
    i18n: { language: "en" },
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
    question_number: 7,
    detected_script: "latin",
    numerology_system: "pythagorean",
    raw_letter_sum: 142,
    is_master_number: false,
    fc60_stamp: null,
    numerology: null,
    moon: null,
    ganzhi: null,
    patterns: null,
    confidence: { score: 85, level: "high" },
    ai_interpretation: "Signs point to yes",
    reading_id: null,
  },
};

const nameResult: ConsultationResult = {
  type: "name",
  data: {
    name: "John Doe",
    detected_script: "latin",
    numerology_system: "pythagorean",
    expression: 3,
    soul_urge: 5,
    personality: 7,
    life_path: null,
    personal_year: null,
    fc60_stamp: null,
    moon: null,
    ganzhi: null,
    patterns: null,
    confidence: { score: 80, level: "high" },
    ai_interpretation: "Creative energy",
    letter_breakdown: [{ letter: "J", value: 1, element: "Fire" }],
    reading_id: null,
  },
};

describe("SummaryTab", () => {
  it("shows placeholder when no result", () => {
    render(<SummaryTab result={null} />);
    expect(
      screen.getByText("Results will appear here after a reading."),
    ).toBeInTheDocument();
  });

  it("reading type shows section-based layout", () => {
    render(<SummaryTab result={readingResult} />);
    // Sections that should be present
    expect(screen.getByText("Core Identity")).toBeInTheDocument();
    expect(screen.getByText("Right Now")).toBeInTheDocument();
    expect(screen.getByText("Patterns & Synchronicities")).toBeInTheDocument();
    expect(screen.getByText("Today's Advice")).toBeInTheDocument();
    // Summary text still present
    expect(
      screen.getByText("This is a test reading summary"),
    ).toBeInTheDocument();
    // Footer confidence
    expect(screen.getByText("Reading Confidence")).toBeInTheDocument();
  });

  it("question type shows simplified sections", () => {
    render(<SummaryTab result={questionResult} />);
    expect(screen.getByText("Will it work?")).toBeInTheDocument();
    expect(screen.getByText("Question")).toBeInTheDocument();
    expect(screen.getByText("Core Identity")).toBeInTheDocument();
    expect(screen.getByText("The Message")).toBeInTheDocument();
    expect(screen.getByText("Signs point to yes")).toBeInTheDocument();
  });

  it("name type shows simplified sections", () => {
    render(<SummaryTab result={nameResult} />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Core Identity")).toBeInTheDocument();
    expect(screen.getByText("Letter Analysis")).toBeInTheDocument();
    expect(screen.getByText("The Message")).toBeInTheDocument();
  });
});
