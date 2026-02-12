import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import Dashboard from "../Dashboard";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "dashboard.welcome_explorer")
        return `${opts?.greeting}, Explorer`;
      if (key === "dashboard.today_date") return `Today is ${opts?.date}`;
      if (key === "dashboard.stats_streak_days") return `${opts?.count} days`;
      if (key === "dashboard.moon_illumination")
        return `${opts?.percent}% illuminated`;
      const map: Record<string, string> = {
        "dashboard.title": "Dashboard",
        "dashboard.welcome_morning": "Good morning",
        "dashboard.welcome_afternoon": "Good afternoon",
        "dashboard.welcome_evening": "Good evening",
        "dashboard.daily_no_reading": "No reading for today.",
        "dashboard.daily_generate": "Generate Today's Reading",
        "dashboard.daily_reading": "Today's Reading",
        "dashboard.stats_total": "Total Readings",
        "dashboard.stats_confidence": "Avg Confidence",
        "dashboard.stats_most_used": "Most Used Type",
        "dashboard.stats_streak": "Streak",
        "dashboard.recent_title": "Recent Readings",
        "dashboard.recent_empty": "No readings yet.",
        "dashboard.recent_start": "Start Reading",
        "dashboard.quick_actions": "Quick Actions",
        "dashboard.quick_time": "Time Reading",
        "dashboard.quick_question": "Ask a Question",
        "dashboard.quick_name": "Name Reading",
      };
      return map[key] ?? key;
    },
    i18n: { language: "en" },
  }),
}));

vi.mock("jalaali-js", () => ({
  toJalaali: () => ({ jy: 1404, jm: 11, jd: 25 }),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => vi.fn(),
  Link: ({
    to,
    children,
    ...props
  }: {
    to: string;
    children: React.ReactNode;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/hooks/useDashboard", () => ({
  useDashboardStats: () => ({ data: undefined, isLoading: false }),
  useRecentReadings: () => ({ data: undefined, isLoading: false }),
  useDailyReading: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
}));

describe("Dashboard", () => {
  it("renders all five sections", () => {
    render(<Dashboard />);
    expect(screen.getByTestId("welcome-banner")).toBeInTheDocument();
    expect(screen.getByTestId("daily-empty")).toBeInTheDocument();
    expect(screen.getByTestId("stats-cards")).toBeInTheDocument();
    expect(screen.getByTestId("recent-readings")).toBeInTheDocument();
    expect(screen.getByTestId("quick-actions")).toBeInTheDocument();
  });

  it("renders quick action buttons", () => {
    render(<Dashboard />);
    expect(screen.getByText("Time Reading")).toBeInTheDocument();
    expect(screen.getByText("Ask a Question")).toBeInTheDocument();
    expect(screen.getByText("Name Reading")).toBeInTheDocument();
  });

  it("renders page title for accessibility", () => {
    render(<Dashboard />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });
});
