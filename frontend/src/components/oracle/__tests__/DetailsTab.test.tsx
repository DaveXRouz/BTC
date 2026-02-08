import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DetailsTab } from "../DetailsTab";
import type { ConsultationResult } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.details_placeholder":
          "Submit a reading to see detailed analysis.",
        "oracle.details_fc60": "FC60 Analysis",
        "oracle.details_numerology": "Numerology",
        "oracle.details_zodiac": "Zodiac",
        "oracle.details_chinese": "Chinese Zodiac",
        "oracle.details_letters": "Letter Analysis",
        "oracle.cycle": "Cycle",
        "oracle.element": "Element",
        "oracle.polarity": "Polarity",
        "oracle.stem": "Stem",
        "oracle.branch": "Branch",
        "oracle.energy": "Energy",
        "oracle.element_balance": "Element Balance",
        "oracle.life_path": "Life Path",
        "oracle.day_vibration": "Day Vibration",
        "oracle.personal_year": "Personal Year",
        "oracle.personal_month": "Personal Month",
        "oracle.personal_day": "Personal Day",
        "oracle.sign_number": "Sign Number",
        "oracle.answer": "Answer",
        "oracle.confidence": "Confidence",
        "oracle.destiny": "Destiny",
        "oracle.soul_urge": "Soul Urge",
        "oracle.personality": "Personality",
      };
      return map[key] ?? key;
    },
  }),
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
    summary: "Test summary",
    generated_at: "2024-01-01T12:00:00Z",
  },
};

const nameResult: ConsultationResult = {
  type: "name",
  data: {
    name: "Alice",
    destiny_number: 7,
    soul_urge: 3,
    personality: 4,
    letters: [
      { letter: "A", value: 1, element: "Fire" },
      { letter: "l", value: 3, element: "Water" },
    ],
    interpretation: "A creative soul",
  },
};

describe("DetailsTab", () => {
  it("shows placeholder when no result", () => {
    render(<DetailsTab result={null} />);
    expect(
      screen.getByText("Submit a reading to see detailed analysis."),
    ).toBeInTheDocument();
  });

  it("shows FC60 section for reading (defaultOpen)", () => {
    render(<DetailsTab result={readingResult} />);
    expect(screen.getByText("FC60 Analysis")).toBeInTheDocument();
    // FC60 section is defaultOpen, so data should be visible
    expect(screen.getByText("Wood")).toBeInTheDocument();
    expect(screen.getByText("Yang")).toBeInTheDocument();
  });

  it("shows Numerology section (collapsed by default)", async () => {
    render(<DetailsTab result={readingResult} />);
    expect(screen.getByText("Numerology")).toBeInTheDocument();
    // Click to expand
    await userEvent.click(screen.getByText("Numerology"));
    expect(screen.getByText("5")).toBeInTheDocument(); // life_path
  });

  it("shows name details with letter table", async () => {
    render(<DetailsTab result={nameResult} />);
    expect(screen.getByText("7")).toBeInTheDocument(); // destiny
    // Letter Analysis is collapsed — expand it
    await userEvent.click(screen.getByText("Letter Analysis"));
    expect(screen.getByText("A")).toBeInTheDocument(); // letter
  });
});
