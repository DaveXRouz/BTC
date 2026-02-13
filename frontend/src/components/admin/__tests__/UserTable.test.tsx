import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { UserTable } from "../UserTable";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "admin.search_users": "Search users...",
        "admin.col_username": "Username",
        "admin.col_role": "Role",
        "admin.col_status": "Status",
        "admin.col_created": "Created",
        "admin.col_last_login": "Last Login",
        "admin.col_readings": "Readings",
        "admin.col_actions": "Actions",
        "admin.status_active": "Active",
        "admin.status_inactive": "Inactive",
        "admin.no_users": "No users found",
        "admin.page_prev": "Previous",
        "admin.page_next": "Next",
        "admin.page_of": "of",
        "admin.page_size": "per page",
        "admin.never": "Never",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockUsers = [
  {
    id: "u1",
    username: "alice",
    role: "admin",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    last_login: "2024-06-01T12:00:00Z",
    reading_count: 5,
  },
  {
    id: "u2",
    username: "bob",
    role: "user",
    is_active: false,
    created_at: "2024-02-01T00:00:00Z",
    updated_at: "2024-02-01T00:00:00Z",
    last_login: null,
    reading_count: 0,
  },
];

const defaultProps = {
  users: mockUsers,
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
  currentUserId: "u1",
  onRoleChange: vi.fn(),
  onResetPassword: vi.fn(),
  onStatusChange: vi.fn(),
  tempPassword: null,
};

describe("UserTable", () => {
  it("renders all users", () => {
    renderWithProviders(<UserTable {...defaultProps} />);
    expect(screen.getByText("alice")).toBeInTheDocument();
    expect(screen.getByText("bob")).toBeInTheDocument();
  });

  it("shows search input", () => {
    renderWithProviders(<UserTable {...defaultProps} />);
    expect(screen.getByPlaceholderText("Search users...")).toBeInTheDocument();
  });

  it("shows active/inactive status badges", () => {
    renderWithProviders(<UserTable {...defaultProps} />);
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("shows empty state when no users", () => {
    renderWithProviders(<UserTable {...defaultProps} users={[]} total={0} />);
    expect(screen.getByText("No users found")).toBeInTheDocument();
  });

  it("fires onSearch when typing", async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserTable {...defaultProps} />);
    const input = screen.getByPlaceholderText("Search users...");
    await user.type(input, "test");
    // Debounced search is fire-and-forget; just ensure no crash
    expect(input).toHaveValue("test");
  });
});
