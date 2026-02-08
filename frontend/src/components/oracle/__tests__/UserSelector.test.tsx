import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserSelector } from "../UserSelector";
import type { OracleUser } from "@/types";

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "common.loading": "Loading...",
        "oracle.select_profile": "Select profile",
        "oracle.no_profiles": "No profiles yet",
        "oracle.add_new_profile": "Add New Profile",
        "oracle.edit_profile": "Edit Profile",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockUsers: OracleUser[] = [
  {
    id: 1,
    name: "Alice",
    birthday: "1990-01-15",
    mother_name: "Carol",
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Bob",
    birthday: "1985-06-20",
    mother_name: "Diana",
    created_at: "2024-01-02T00:00:00Z",
  },
];

const defaultProps = {
  users: mockUsers,
  selectedId: null as number | null,
  onSelect: vi.fn(),
  onAddNew: vi.fn(),
  onEdit: vi.fn(),
};

describe("UserSelector", () => {
  it("shows loading state", () => {
    render(<UserSelector {...defaultProps} isLoading />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows empty state when no users", () => {
    render(<UserSelector {...defaultProps} users={[]} />);
    const select = screen.getByLabelText("Select profile");
    expect(select).toBeInTheDocument();
    expect(screen.getByText("No profiles yet")).toBeInTheDocument();
  });

  it("renders user options", () => {
    render(<UserSelector {...defaultProps} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("calls onSelect when user is chosen", async () => {
    const onSelect = vi.fn();
    render(<UserSelector {...defaultProps} onSelect={onSelect} />);
    const select = screen.getByLabelText("Select profile");
    await userEvent.selectOptions(select, "1");
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onAddNew when add button clicked", async () => {
    const onAddNew = vi.fn();
    render(<UserSelector {...defaultProps} onAddNew={onAddNew} />);
    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(onAddNew).toHaveBeenCalled();
  });

  it("shows edit button only when user is selected", () => {
    const { rerender } = render(<UserSelector {...defaultProps} />);
    expect(screen.queryByText("Edit Profile")).not.toBeInTheDocument();

    rerender(<UserSelector {...defaultProps} selectedId={1} />);
    expect(screen.getByText("Edit Profile")).toBeInTheDocument();
  });

  it("calls onEdit when edit button clicked", async () => {
    const onEdit = vi.fn();
    render(<UserSelector {...defaultProps} selectedId={1} onEdit={onEdit} />);
    await userEvent.click(screen.getByText("Edit Profile"));
    expect(onEdit).toHaveBeenCalled();
  });
});
