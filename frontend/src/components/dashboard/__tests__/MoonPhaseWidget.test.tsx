import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MoonPhaseWidget } from "../MoonPhaseWidget";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "dashboard.moon_illumination")
        return `${opts?.percent}% illuminated`;
      return key;
    },
  }),
}));

describe("MoonPhaseWidget", () => {
  it("renders moon emoji, phase name, and illumination", () => {
    render(
      <MoonPhaseWidget
        moonData={{ phase_name: "Full Moon", illumination: 0.97, emoji: "🌕" }}
      />,
    );
    expect(screen.getByText("🌕")).toBeInTheDocument();
    expect(screen.getByText("Full Moon")).toBeInTheDocument();
    expect(screen.getByText("97% illuminated")).toBeInTheDocument();
  });

  it("renders loading skeleton when isLoading", () => {
    render(<MoonPhaseWidget isLoading />);
    expect(screen.getByTestId("moon-loading")).toBeInTheDocument();
  });

  it("renders nothing when no moonData and not loading", () => {
    const { container } = render(<MoonPhaseWidget />);
    expect(container.innerHTML).toBe("");
  });
});
