import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../../App";

vi.mock("../../hooks/useTheme", () => ({
  useTheme: () => ({
    resolvedTheme: "dark",
    toggleTheme: vi.fn(),
    theme: "dark",
    setTheme: vi.fn(),
  }),
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

vi.mock("react-i18next", async () => {
  const original = await vi.importActual("react-i18next");
  return {
    ...original,
    useTranslation: () => ({
      t: (key: string) => {
        const map: Record<string, string> = {
          "layout.app_tagline": "Numerology Puzzle Solver",
          "layout.sidebar_collapse": "Collapse sidebar",
          "layout.sidebar_expand": "Expand sidebar",
          "layout.mobile_menu": "Open menu",
          "layout.footer_copyright": "NPS Project",
          "layout.version": "v4.0.0",
          "layout.theme_toggle": "Toggle theme",
          "layout.coming_soon": "Coming Soon",
          "nav.dashboard": "Dashboard",
          "nav.oracle": "Oracle",
          "nav.history": "Reading History",
          "nav.settings": "Settings",
          "nav.scanner": "Scanner",
          "nav.admin": "Admin Panel",
        };
        return map[key] ?? key;
      },
      i18n: {
        language: "en",
        changeLanguage: vi.fn(),
      },
    }),
    withTranslation: () => (Component: React.ComponentType) => Component,
  };
});

vi.mock("../Dashboard", () => ({
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}));
vi.mock("../Oracle", () => ({
  default: () => <div data-testid="oracle-page">Oracle Page</div>,
}));
vi.mock("../ReadingHistory", () => ({
  default: () => <div data-testid="history-page">History Page</div>,
}));
vi.mock("../Settings", () => ({
  default: () => <div data-testid="settings-page">Settings Page</div>,
}));
vi.mock("../AdminPanel", () => ({
  default: () => <div data-testid="admin-page">Admin Page</div>,
}));
vi.mock("../Scanner", () => ({
  default: () => <div data-testid="scanner-page">Scanner Page</div>,
}));

function renderApp(initialRoute = "/") {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App routing", () => {
  it("root redirects to dashboard", async () => {
    renderApp("/");
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-page")).toBeInTheDocument();
    });
  });

  it("renders dashboard route", async () => {
    renderApp("/dashboard");
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-page")).toBeInTheDocument();
    });
  });

  it("renders oracle route", async () => {
    renderApp("/oracle");
    await waitFor(() => {
      expect(screen.getByTestId("oracle-page")).toBeInTheDocument();
    });
  });

  it("renders history route", async () => {
    renderApp("/history");
    await waitFor(() => {
      expect(screen.getByTestId("history-page")).toBeInTheDocument();
    });
  });

  it("renders settings route", async () => {
    renderApp("/settings");
    await waitFor(() => {
      expect(screen.getByTestId("settings-page")).toBeInTheDocument();
    });
  });
});
