import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/testUtils";
import { ProfileTable } from "../ProfileTable";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "admin.search_profiles": "Search profiles...",
        "admin.col_name": "Name",
        "admin.col_name_persian": "Name (Persian)",
        "admin.col_birthday": "Birthday",
        "admin.col_readings": "Readings",
        "admin.col_actions": "Actions",
        "admin.status_deleted": "Deleted",
        "admin.no_profiles": "No profiles found",
        "admin.page_prev": "Previous",
        "admin.page_next": "Next",
        "admin.page_of": "of",
        "admin.page_size": "per page",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockProfiles = [
  {
    id: 1,
    name: "Alice Doe",
    name_persian: "آلیس دو",
    birthday: "1990-05-15",
    country: "US",
    city: "NYC",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    deleted_at: null,
    reading_count: 3,
  },
  {
    id: 2,
    name: "Bob Smith",
    name_persian: null,
    birthday: "1985-10-20",
    country: "UK",
    city: "London",
    created_at: "2024-02-01T00:00:00Z",
    updated_at: "2024-02-01T00:00:00Z",
    deleted_at: "2024-03-01T00:00:00Z",
    reading_count: 0,
  },
];

const defaultProps = {
  profiles: mockProfiles,
  total: 2,
  loading: false,
  sortBy: "created_at" as const,
  sortOrder: "desc" as const,
  onSort: vi.fn(),
  onSearch: vi.fn(),
  page: 0,
  pageSize: 20,
  onPageChange: vi.fn(),
  onPageSizeChange: vi.fn(),
  onDelete: vi.fn(),
};

describe("ProfileTable", () => {
  it("renders all profiles", () => {
    renderWithProviders(<ProfileTable {...defaultProps} />);
    expect(screen.getByText("Alice Doe")).toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();
  });

  it("shows deleted badge for soft-deleted profiles", () => {
    renderWithProviders(<ProfileTable {...defaultProps} />);
    const deletedElements = screen.getAllByText("Deleted");
    expect(deletedElements.length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no profiles", () => {
    renderWithProviders(
      <ProfileTable {...defaultProps} profiles={[]} total={0} />,
    );
    expect(screen.getByText("No profiles found")).toBeInTheDocument();
  });
});
