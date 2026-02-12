import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import GanzhiDisplay from "../GanzhiDisplay";
import type { GanzhiFullData } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "oracle.cosmic.year_cycle": "Year Cycle",
        "oracle.cosmic.day_cycle": "Day Cycle",
        "oracle.cosmic.hour_cycle": "Hour Cycle",
      };
      return translations[key] || key;
    },
    i18n: { language: "en" },
  }),
}));

const sampleGanzhi: GanzhiFullData = {
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
};

describe("GanzhiDisplay", () => {
  it("renders year animal name and element", () => {
    render(<GanzhiDisplay ganzhi={sampleGanzhi} />);
    expect(screen.getByText("Horse")).toBeInTheDocument();
    expect(screen.getByText("Fire")).toBeInTheDocument();
  });

  it("renders traditional name", () => {
    render(<GanzhiDisplay ganzhi={sampleGanzhi} />);
    expect(screen.getByText("Fire Horse")).toBeInTheDocument();
  });

  it("renders day cycle when data present", () => {
    render(<GanzhiDisplay ganzhi={sampleGanzhi} />);
    expect(screen.getByText("Day Cycle")).toBeInTheDocument();
    expect(screen.getByText("Rat")).toBeInTheDocument();
    expect(screen.getByText("Wood")).toBeInTheDocument();
  });

  it("conditionally renders hour cycle", () => {
    const withHour: GanzhiFullData = {
      ...sampleGanzhi,
      hour: { animal_name: "Tiger" },
    };
    render(<GanzhiDisplay ganzhi={withHour} />);
    expect(screen.getByText("Hour Cycle")).toBeInTheDocument();
    expect(screen.getByText("Tiger")).toBeInTheDocument();
  });

  it("compact mode shows only year cycle", () => {
    const withHour: GanzhiFullData = {
      ...sampleGanzhi,
      hour: { animal_name: "Tiger" },
    };
    render(<GanzhiDisplay ganzhi={withHour} compact />);
    expect(screen.getByText("Horse")).toBeInTheDocument();
    expect(screen.queryByText("Day Cycle")).not.toBeInTheDocument();
    expect(screen.queryByText("Hour Cycle")).not.toBeInTheDocument();
  });
});
