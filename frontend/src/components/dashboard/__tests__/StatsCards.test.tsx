import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatsCards } from "../StatsCards";
import type { DashboardStats } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const map: Record<string, string> = {
        "dashboard.stats_total": "Total Readings",
        "dashboard.stats_confidence": "Avg Confidence",
        "dashboard.stats_most_used": "Most Used Type",
        "dashboard.stats_streak": "Streak",
        "dashboard.type_time": "Time",
      };
      if (key === "dashboard.stats_streak_days") return `${opts?.count} days`;
      return map[key] ?? key;
    },
    i18n: { language: "en" },
  }),
}));

const mockStats: DashboardStats = {
  total_readings: 42,
  readings_by_type: { time: 20, name: 12, question: 10 },
  average_confidence: 0.73,
  most_used_type: "time",
  streak_days: 5,
  readings_today: 3,
  readings_this_week: 15,
  readings_this_month: 42,
};

describe("StatsCards", () => {
  it("renders four stat cards with correct values", () => {
    render(<StatsCards stats={mockStats} isLoading={false} />);
    expect(screen.getByTestId("stats-cards")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("73%")).toBeInTheDocument();
    expect(screen.getByText("Time")).toBeInTheDocument();
    expect(screen.getByText("5 days")).toBeInTheDocument();
  });

  it("shows loading skeletons when isLoading", () => {
    render(<StatsCards isLoading={true} />);
    expect(screen.getByTestId("stats-loading")).toBeInTheDocument();
  });

  it("handles zero stats gracefully", () => {
    const zeroStats: DashboardStats = {
      total_readings: 0,
      readings_by_type: {},
      average_confidence: null,
      most_used_type: null,
      streak_days: 0,
      readings_today: 0,
      readings_this_week: 0,
      readings_this_month: 0,
    };
    render(<StatsCards stats={zeroStats} isLoading={false} />);
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("0 days")).toBeInTheDocument();
  });
});
