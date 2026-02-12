import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DailyReadingCard } from "../DailyReadingCard";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "dashboard.daily_reading": "Today's Reading",
        "dashboard.daily_generate": "Generate Today's Reading",
        "dashboard.daily_no_reading": "No reading generated for today yet.",
        "dashboard.daily_error": "Could not load daily reading.",
        "dashboard.daily_retry": "Retry",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("DailyReadingCard", () => {
  it("renders reading summary when data provided", () => {
    render(
      <DailyReadingCard
        dailyReading={{
          date: "2026-02-13",
          summary: "A balanced day ahead.",
        }}
        isLoading={false}
        isError={false}
        onRetry={() => {}}
      />,
    );
    expect(screen.getByText("A balanced day ahead.")).toBeInTheDocument();
    expect(screen.getByTestId("daily-card")).toBeInTheDocument();
  });

  it("shows generate button when no reading exists", async () => {
    render(
      <DailyReadingCard
        dailyReading={null}
        isLoading={false}
        isError={false}
        onRetry={() => {}}
      />,
    );
    const btn = screen.getByTestId("generate-daily-btn");
    expect(btn).toBeInTheDocument();
    await userEvent.click(btn);
    expect(mockNavigate).toHaveBeenCalledWith("/oracle?type=daily");
  });

  it("shows loading skeleton during fetch", () => {
    render(
      <DailyReadingCard isLoading={true} isError={false} onRetry={() => {}} />,
    );
    expect(screen.getByTestId("daily-loading")).toBeInTheDocument();
  });

  it("shows error state with retry button", async () => {
    const onRetry = vi.fn();
    render(
      <DailyReadingCard isLoading={false} isError={true} onRetry={onRetry} />,
    );
    expect(screen.getByTestId("daily-error")).toBeInTheDocument();
    await userEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalled();
  });
});
