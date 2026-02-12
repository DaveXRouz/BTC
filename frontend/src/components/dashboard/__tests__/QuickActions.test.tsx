import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuickActions } from "../QuickActions";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "dashboard.quick_actions": "Quick Actions",
        "dashboard.quick_time": "Time Reading",
        "dashboard.quick_question": "Ask a Question",
        "dashboard.quick_name": "Name Reading",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("QuickActions", () => {
  beforeEach(() => mockNavigate.mockClear());

  it("renders three action buttons with correct labels", () => {
    render(<QuickActions />);
    expect(screen.getByText("Time Reading")).toBeInTheDocument();
    expect(screen.getByText("Ask a Question")).toBeInTheDocument();
    expect(screen.getByText("Name Reading")).toBeInTheDocument();
  });

  it("navigates to oracle with type=time on click", async () => {
    render(<QuickActions />);
    await userEvent.click(screen.getByTestId("quick-time"));
    expect(mockNavigate).toHaveBeenCalledWith("/oracle?type=time");
  });

  it("navigates to oracle with type=question on click", async () => {
    render(<QuickActions />);
    await userEvent.click(screen.getByTestId("quick-question"));
    expect(mockNavigate).toHaveBeenCalledWith("/oracle?type=question");
  });

  it("navigates to oracle with type=name on click", async () => {
    render(<QuickActions />);
    await userEvent.click(screen.getByTestId("quick-name"));
    expect(mockNavigate).toHaveBeenCalledWith("/oracle?type=name");
  });
});
