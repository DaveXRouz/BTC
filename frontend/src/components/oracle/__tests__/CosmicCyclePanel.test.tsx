import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import CosmicCyclePanel from "../CosmicCyclePanel";
import type { CosmicCycleData } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "oracle.cosmic.title": "Cosmic Cycles",
        "oracle.cosmic.moon_title": "Moon Phase",
        "oracle.cosmic.ganzhi_title": "Chinese Zodiac",
        "oracle.cosmic.current_title": "Current Moment",
        "oracle.cosmic.planet_moon_title": "Planet-Moon Insight",
        "oracle.cosmic.ruling_planet": "Ruling Planet",
        "oracle.cosmic.domain": "Domain",
        "oracle.cosmic.no_data": "No cosmic data available",
        "oracle.cosmic.illumination": "Illumination",
        "oracle.cosmic.moon_age": "Moon Age",
        "oracle.cosmic.days": "days",
        "oracle.cosmic.energy": "Energy",
        "oracle.cosmic.best_for": "Best For",
        "oracle.cosmic.avoid": "Avoid",
        "oracle.cosmic.year_cycle": "Year Cycle",
        "oracle.cosmic.day_cycle": "Day Cycle",
        "oracle.cosmic.hour_cycle": "Hour Cycle",
      };
      return translations[key] || key;
    },
    i18n: { language: "en" },
  }),
}));

const fullData: CosmicCycleData = {
  moon: {
    phase_name: "Full Moon",
    emoji: "\uD83C\uDF15",
    age: 14.77,
    illumination: 99.8,
    energy: "Culminate",
    best_for: "Celebrating",
    avoid: "Starting",
  },
  ganzhi: {
    year: {
      animal_name: "Horse",
      element: "Fire",
      polarity: "Yang",
      gz_token: "BI-HO",
      traditional_name: "Fire Horse",
    },
    day: {
      animal_name: "Rat",
      element: "Wood",
      polarity: "Yang",
      gz_token: "JA-RA",
    },
  },
  current: {
    weekday: "Friday",
    planet: "Venus",
    domain: "Love, values, beauty",
  },
  planet_moon: {
    theme: "Love Illuminated",
    message: "Venus and Full Moon combine for heightened beauty.",
  },
};

describe("CosmicCyclePanel", () => {
  it("renders all three sections with complete data", () => {
    render(<CosmicCyclePanel cosmicData={fullData} />);
    expect(screen.getByText("Cosmic Cycles")).toBeInTheDocument();
    expect(screen.getByText("Moon Phase")).toBeInTheDocument();
    expect(screen.getByText("Chinese Zodiac")).toBeInTheDocument();
    expect(screen.getByText("Current Moment")).toBeInTheDocument();
  });

  it("handles null moon data gracefully", () => {
    const data: CosmicCycleData = {
      ...fullData,
      moon: null,
      planet_moon: null,
    };
    render(<CosmicCyclePanel cosmicData={data} />);
    expect(screen.queryByText("Moon Phase")).not.toBeInTheDocument();
    expect(screen.getByText("Chinese Zodiac")).toBeInTheDocument();
  });

  it("handles null ganzhi data gracefully", () => {
    const data: CosmicCycleData = { ...fullData, ganzhi: null };
    render(<CosmicCyclePanel cosmicData={data} />);
    expect(screen.queryByText("Chinese Zodiac")).not.toBeInTheDocument();
    expect(screen.getByText("Moon Phase")).toBeInTheDocument();
  });

  it("renders planet-moon insight when present", () => {
    render(<CosmicCyclePanel cosmicData={fullData} />);
    expect(screen.getByText("Planet-Moon Insight")).toBeInTheDocument();
    expect(screen.getByText("Love Illuminated")).toBeInTheDocument();
    expect(
      screen.getByText("Venus and Full Moon combine for heightened beauty."),
    ).toBeInTheDocument();
  });

  it("shows placeholder when all data is null", () => {
    const emptyData: CosmicCycleData = {
      moon: null,
      ganzhi: null,
      current: null,
      planet_moon: null,
    };
    render(<CosmicCyclePanel cosmicData={emptyData} />);
    expect(screen.getByText("No cosmic data available")).toBeInTheDocument();
  });
});
