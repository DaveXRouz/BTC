import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { WelcomeBanner } from "../WelcomeBanner";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "dashboard.welcome_morning") return "Good morning";
      if (key === "dashboard.welcome_afternoon") return "Good afternoon";
      if (key === "dashboard.welcome_evening") return "Good evening";
      if (key === "dashboard.welcome_user")
        return `${opts?.greeting}, ${opts?.name}`;
      if (key === "dashboard.welcome_explorer")
        return `${opts?.greeting}, Explorer`;
      if (key === "dashboard.today_date") return `Today is ${opts?.date}`;
      if (key === "dashboard.moon_illumination")
        return `${opts?.percent}% illuminated`;
      return key;
    },
    i18n: { language: "en" },
  }),
}));

vi.mock("jalaali-js", () => ({
  toJalaali: () => ({ jy: 1404, jm: 11, jd: 25 }),
}));

describe("WelcomeBanner", () => {
  it("renders greeting with user name", () => {
    render(<WelcomeBanner userName="Dave" />);
    const banner = screen.getByTestId("welcome-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toContain("Dave");
  });

  it("renders explorer greeting when no user name", () => {
    render(<WelcomeBanner />);
    expect(screen.getByTestId("welcome-banner").textContent).toContain(
      "Explorer",
    );
  });

  it("renders today's date", () => {
    render(<WelcomeBanner />);
    expect(screen.getByTestId("welcome-banner").textContent).toContain(
      "Today is",
    );
  });

  it("renders moon widget when moonData provided", () => {
    render(
      <WelcomeBanner
        moonData={{ phase_name: "Full Moon", illumination: 0.97, emoji: "🌕" }}
      />,
    );
    expect(screen.getByTestId("moon-widget")).toBeInTheDocument();
  });
});
