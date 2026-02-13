import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/testUtils";
import { AdminGuard } from "../AdminGuard";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "admin.forbidden_title": "Access Denied",
        "admin.forbidden_message":
          "You need admin privileges to access this page.",
      };
      return map[key] ?? key;
    },
  }),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet">Admin Content</div>,
  };
});

describe("AdminGuard", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders outlet for admin role", () => {
    localStorage.setItem("nps_user_role", "admin");
    renderWithProviders(<AdminGuard />);
    expect(screen.getByTestId("outlet")).toBeInTheDocument();
  });

  it("renders forbidden message for non-admin", () => {
    localStorage.setItem("nps_user_role", "user");
    renderWithProviders(<AdminGuard />);
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(
      screen.getByText("You need admin privileges to access this page."),
    ).toBeInTheDocument();
  });

  it("renders forbidden message when no role is set", () => {
    renderWithProviders(<AdminGuard />);
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
