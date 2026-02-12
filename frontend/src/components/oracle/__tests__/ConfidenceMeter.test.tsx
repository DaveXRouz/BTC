import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConfidenceMeter } from "../ConfidenceMeter";
import type { ConfidenceData, ConfidenceBoost } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const map: Record<string, string> = {
        "oracle.confidence_label": "Reading Confidence",
        "oracle.confidence_score": "{{score}}%",
        "oracle.confidence_level_low": "Low Confidence",
        "oracle.confidence_level_medium": "Medium Confidence",
        "oracle.confidence_level_high": "High Confidence",
        "oracle.confidence_level_very_high": "Very High Confidence",
        "oracle.confidence_boost_add": "Add to boost",
        "oracle.confidence_factors": "Based on {{count}} data sources",
        "oracle.confidence_priority_hint":
          "Input priority: heartbeat > location > time > name > gender > DOB > mother",
      };
      let text = map[key] ?? key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          text = text.replace(`{{${k}}}`, String(v));
        }
      }
      return text;
    },
  }),
}));

const BOOSTS: ConfidenceBoost[] = [
  { field: "mother", label: "Mother's name", boost: 10, filled: true },
  { field: "location", label: "Location", boost: 5, filled: true },
  { field: "heartbeat", label: "Heart rate", boost: 5, filled: false },
  { field: "time", label: "Exact time", boost: 5, filled: false },
];

describe("ConfidenceMeter", () => {
  it("renders progress bar with correct width", () => {
    const conf: ConfidenceData = { score: 80, level: "high", factors: "4" };
    render(<ConfidenceMeter confidence={conf} boosts={BOOSTS} />);
    const fill = screen.getByTestId("confidence-fill");
    expect(fill.style.width).toBe("80%");
  });

  it("shows correct color for high confidence", () => {
    const conf: ConfidenceData = { score: 80, level: "high", factors: "4" };
    render(<ConfidenceMeter confidence={conf} boosts={[]} />);
    const fill = screen.getByTestId("confidence-fill");
    expect(fill.className).toContain("bg-blue-600");
  });

  it("shows correct color for low confidence", () => {
    const conf: ConfidenceData = { score: 55, level: "low", factors: "2" };
    render(<ConfidenceMeter confidence={conf} boosts={[]} />);
    const fill = screen.getByTestId("confidence-fill");
    expect(fill.className).toContain("bg-red-600");
  });

  it("displays completeness breakdown", () => {
    const conf: ConfidenceData = { score: 75, level: "high", factors: "4" };
    render(<ConfidenceMeter confidence={conf} boosts={BOOSTS} />);
    expect(screen.getByTestId("confidence-boosts")).toBeDefined();
    expect(screen.getByTestId("boost-mother")).toBeDefined();
    expect(screen.getByTestId("boost-heartbeat")).toBeDefined();
  });

  it("marks filled fields with checkmark", () => {
    const conf: ConfidenceData = { score: 75, level: "high", factors: "4" };
    render(<ConfidenceMeter confidence={conf} boosts={BOOSTS} />);
    const motherIcon = screen.getByTestId("boost-icon-mother");
    expect(motherIcon.textContent).toBe("✓");
    const heartbeatIcon = screen.getByTestId("boost-icon-heartbeat");
    expect(heartbeatIcon.textContent).toBe("○");
  });

  it("shows 'Add to boost' for unfilled fields", () => {
    const conf: ConfidenceData = { score: 75, level: "high", factors: "4" };
    render(<ConfidenceMeter confidence={conf} boosts={BOOSTS} />);
    const addLinks = screen.getAllByText("Add to boost");
    expect(addLinks.length).toBe(2); // heartbeat and time are unfilled
  });

  it("renders skeleton when confidence is null", () => {
    render(<ConfidenceMeter confidence={null} boosts={[]} />);
    expect(screen.getByTestId("confidence-skeleton")).toBeDefined();
  });
});
