import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RecentReadings } from "../RecentReadings";
import type { StoredReading } from "@/types";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
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

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "dashboard.recent_title": "Recent Readings",
        "dashboard.recent_view_all": "View All",
        "dashboard.recent_empty": "No readings yet. Start your first reading!",
        "dashboard.recent_start": "Start Reading",
        "dashboard.type_time": "Time",
        "dashboard.type_name": "Name",
      };
      return map[key] ?? key;
    },
  }),
}));

function makeReading(overrides: Partial<StoredReading> = {}): StoredReading {
  return {
    id: 1,
    user_id: null,
    sign_type: "time",
    sign_value: "12:30:00",
    question: null,
    reading_result: null,
    ai_interpretation: null,
    created_at: "2026-02-13T10:00:00Z",
    is_favorite: false,
    deleted_at: null,
    ...overrides,
  };
}

describe("RecentReadings", () => {
  it("renders correct number of reading cards", () => {
    const readings = [
      makeReading({ id: 1 }),
      makeReading({ id: 2, sign_type: "name", sign_value: "Alice" }),
    ];
    render(
      <RecentReadings
        readings={readings}
        isLoading={false}
        isError={false}
        total={2}
      />,
    );
    expect(screen.getAllByTestId("reading-card")).toHaveLength(2);
  });

  it("shows type badges", () => {
    render(
      <RecentReadings
        readings={[makeReading()]}
        isLoading={false}
        isError={false}
        total={1}
      />,
    );
    expect(screen.getByTestId("type-badge")).toHaveTextContent("Time");
  });

  it("renders empty state CTA", () => {
    render(
      <RecentReadings
        readings={[]}
        isLoading={false}
        isError={false}
        total={0}
      />,
    );
    expect(
      screen.getByText("No readings yet. Start your first reading!"),
    ).toBeInTheDocument();
    expect(screen.getByText("Start Reading")).toBeInTheDocument();
  });

  it("click navigates to reading detail", async () => {
    render(
      <RecentReadings
        readings={[makeReading({ id: 42 })]}
        isLoading={false}
        isError={false}
        total={1}
      />,
    );
    await userEvent.click(screen.getByTestId("reading-card"));
    expect(mockNavigate).toHaveBeenCalledWith("/oracle?reading=42");
  });

  it("shows loading skeleton", () => {
    render(
      <RecentReadings
        readings={[]}
        isLoading={true}
        isError={false}
        total={0}
      />,
    );
    expect(screen.getByTestId("recent-loading")).toBeInTheDocument();
  });

  it("shows View All link when total > 5", () => {
    render(
      <RecentReadings
        readings={[makeReading()]}
        isLoading={false}
        isError={false}
        total={10}
      />,
    );
    expect(screen.getByText("View All")).toBeInTheDocument();
  });
});
