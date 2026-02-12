import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import MoonPhaseDisplay from "../MoonPhaseDisplay";
import type { MoonPhaseData } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "oracle.cosmic.illumination": "Illumination",
        "oracle.cosmic.moon_age": "Moon Age",
        "oracle.cosmic.days": "days",
        "oracle.cosmic.energy": "Energy",
        "oracle.cosmic.best_for": "Best For",
        "oracle.cosmic.avoid": "Avoid",
      };
      return translations[key] || key;
    },
    i18n: { language: "en" },
  }),
}));

const sampleMoon: MoonPhaseData = {
  phase_name: "Full Moon",
  emoji: "\uD83C\uDF15",
  age: 14.77,
  illumination: 99.8,
  energy: "Culminate",
  best_for: "Celebrating achievements",
  avoid: "Starting new projects",
};

describe("MoonPhaseDisplay", () => {
  it("renders moon emoji and phase name", () => {
    render(<MoonPhaseDisplay moon={sampleMoon} />);
    expect(screen.getByText("\uD83C\uDF15")).toBeInTheDocument();
    expect(screen.getByText("Full Moon")).toBeInTheDocument();
  });

  it("renders illumination progress bar with correct percentage", () => {
    render(<MoonPhaseDisplay moon={sampleMoon} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "99.8");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
    expect(screen.getByText("99.8%")).toBeInTheDocument();
  });

  it("renders energy badge", () => {
    render(<MoonPhaseDisplay moon={sampleMoon} />);
    expect(screen.getByText("Culminate")).toBeInTheDocument();
    expect(screen.getByText("Energy:")).toBeInTheDocument();
  });

  it("renders best_for and avoid sections", () => {
    render(<MoonPhaseDisplay moon={sampleMoon} />);
    expect(screen.getByText("Best For")).toBeInTheDocument();
    expect(screen.getByText("Celebrating achievements")).toBeInTheDocument();
    expect(screen.getByText("Avoid")).toBeInTheDocument();
    expect(screen.getByText("Starting new projects")).toBeInTheDocument();
  });

  it("compact mode hides best_for and avoid", () => {
    render(<MoonPhaseDisplay moon={sampleMoon} compact />);
    expect(screen.queryByText("Best For")).not.toBeInTheDocument();
    expect(screen.queryByText("Avoid")).not.toBeInTheDocument();
    // Still shows phase name and illumination
    expect(screen.getByText("Full Moon")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });
});
