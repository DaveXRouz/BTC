import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Layout } from "../Layout";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "layout.app_tagline": "Numerology Puzzle Solver",
        "layout.sidebar_collapse": "Collapse sidebar",
        "layout.sidebar_expand": "Expand sidebar",
        "layout.mobile_menu": "Open menu",
        "layout.mobile_menu_close": "Close menu",
        "layout.footer_copyright": "NPS Project",
        "layout.version": "v4.0.0",
        "layout.theme_toggle": "Toggle theme",
        "layout.coming_soon": "Coming Soon",
        "nav.dashboard": "Dashboard",
        "nav.oracle": "Oracle",
        "nav.history": "Reading History",
        "nav.settings": "Settings",
        "nav.scanner": "Scanner",
      };
      return map[key] ?? key;
    },
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

vi.mock("../../hooks/useTheme", () => ({
  useTheme: () => ({
    resolvedTheme: "dark",
    toggleTheme: vi.fn(),
    theme: "dark",
    setTheme: vi.fn(),
  }),
}));

vi.mock("../../hooks/useDirection", () => ({
  useDirection: () => ({ dir: "ltr", isRTL: false, locale: "en" }),
}));

vi.mock("../../hooks/useWebSocket", () => ({
  useWebSocketConnection: () => undefined,
}));

vi.mock("../../hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => true,
}));

vi.mock("../../hooks/useToast", () => ({
  useToast: () => ({ toasts: [], addToast: vi.fn(), dismissToast: vi.fn() }),
  ToastContext: {
    Provider: ({ children }: { children: React.ReactNode }) => children,
  },
}));

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <Layout />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.clear();
});

describe("Layout", () => {
  it("renders sidebar and content area", () => {
    renderLayout();
    expect(screen.getAllByText("NPS").length).toBeGreaterThan(0);
    expect(screen.getByText("Numerology Puzzle Solver")).toBeInTheDocument();
    expect(screen.getAllByRole("navigation").length).toBeGreaterThan(0);
  });

  it("renders footer with version", () => {
    renderLayout();
    expect(screen.getByText(/v4\.0\.0/)).toBeInTheDocument();
    expect(screen.getByText(/NPS Project/)).toBeInTheDocument();
  });

  it("sidebar collapse toggle works", async () => {
    renderLayout();
    const collapseBtn = screen.getByLabelText("Collapse sidebar");
    await userEvent.click(collapseBtn);
    expect(localStorage.getItem("nps_sidebar_collapsed")).toBe("true");
  });

  it("mobile hamburger button exists", () => {
    renderLayout();
    expect(screen.getByLabelText("Open menu")).toBeInTheDocument();
  });

  it("sidebar collapse persists to localStorage", async () => {
    renderLayout();
    const collapseBtn = screen.getByLabelText("Collapse sidebar");
    await userEvent.click(collapseBtn);
    expect(localStorage.getItem("nps_sidebar_collapsed")).toBe("true");
    const expandBtn = screen.getByLabelText("Expand sidebar");
    await userEvent.click(expandBtn);
    expect(localStorage.getItem("nps_sidebar_collapsed")).toBe("false");
  });

  it("sidebar aside has hidden lg:flex classes for responsive hiding", () => {
    renderLayout();
    const aside = document.querySelector("aside");
    expect(aside).toBeDefined();
    expect(aside?.className).toContain("hidden");
    expect(aside?.className).toContain("lg:flex");
  });

  it("hamburger has lg:hidden class for responsive showing", () => {
    renderLayout();
    const hamburger = screen.getByLabelText("Open menu");
    expect(hamburger.className).toContain("lg:hidden");
  });

  it("opens mobile drawer on hamburger click", async () => {
    renderLayout();
    const hamburger = screen.getByLabelText("Open menu");
    await userEvent.click(hamburger);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("main content has responsive padding classes", () => {
    renderLayout();
    const main = document.querySelector("main");
    expect(main?.className).toContain("p-4");
    expect(main?.className).toContain("lg:p-6");
  });
});
