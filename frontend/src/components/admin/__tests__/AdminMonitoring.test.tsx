import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/test/testUtils";
import { AdminMonitoring } from "@/pages/AdminMonitoring";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "admin.monitoring_system_monitoring": "System Monitoring",
        "admin.monitoring_tab_health": "Health",
        "admin.monitoring_tab_logs": "Logs",
        "admin.monitoring_tab_analytics": "Analytics",
      };
      return map[key] ?? key;
    },
  }),
}));

vi.mock("@/services/api", () => ({
  adminHealth: {
    detailed: vi.fn().mockResolvedValue({
      status: "healthy",
      uptime_seconds: 3600,
      system: {
        python_version: "3.11.0",
        process_memory_mb: 120,
        cpu_count: 4,
        platform: "Linux",
      },
      services: {
        database: { status: "healthy" },
        api: { status: "healthy", version: "4.0.0" },
      },
    }),
    logs: vi.fn().mockResolvedValue({
      logs: [],
      total: 0,
      limit: 25,
      offset: 0,
    }),
    analytics: vi.fn().mockResolvedValue({
      readings_per_day: [],
      readings_by_type: [],
      confidence_trend: [],
      popular_hours: [],
      totals: {
        total_readings: 0,
        avg_confidence: 0,
        most_popular_type: null,
        most_active_hour: null,
        error_count: 0,
      },
    }),
  },
}));

describe("AdminMonitoring", () => {
  it("renders tab navigation with three tabs", () => {
    renderWithProviders(<AdminMonitoring />);
    expect(screen.getByText("Health")).toBeInTheDocument();
    expect(screen.getByText("Logs")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();
  });

  it("shows System Monitoring heading", () => {
    renderWithProviders(<AdminMonitoring />);
    expect(screen.getByText("System Monitoring")).toBeInTheDocument();
  });

  it("defaults to Health tab", () => {
    renderWithProviders(<AdminMonitoring />);
    const healthBtn = screen.getByText("Health");
    expect(healthBtn.className).toContain("bg-blue-600");
  });

  it("switches tabs on click", () => {
    renderWithProviders(<AdminMonitoring />);
    const logsTab = screen.getByText("Logs");
    fireEvent.click(logsTab);
    expect(logsTab.className).toContain("bg-blue-600");
  });
});
