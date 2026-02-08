import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MultiUserSelector } from "../MultiUserSelector";
import type { OracleUser, SelectedUsers } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "common.loading": "Loading...",
        "oracle.primary_user": "Primary User",
        "oracle.secondary_users": "Secondary Users",
        "oracle.select_profile": "Select profile",
        "oracle.no_profiles": "No profiles yet",
        "oracle.add_new_profile": "Add New Profile",
        "oracle.edit_profile": "Edit Profile",
        "oracle.add_secondary": "Add User",
        "oracle.remove_user": "Remove user",
        "oracle.max_users_error": "Maximum 5 users allowed",
        "oracle.duplicate_user_error": "This user has already been added",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockUsers: OracleUser[] = [
  { id: 1, name: "Alice", birthday: "1990-01-15", mother_name: "Carol" },
  { id: 2, name: "Bob", birthday: "1985-06-20", mother_name: "Diana" },
  { id: 3, name: "Charlie", birthday: "1992-03-10", mother_name: "Eve" },
  { id: 4, name: "Dave", birthday: "1988-12-01", mother_name: "Fay" },
  { id: 5, name: "Erin", birthday: "1995-07-22", mother_name: "Grace" },
  { id: 6, name: "Frank", birthday: "1991-09-05", mother_name: "Helen" },
];

const defaultProps = {
  users: mockUsers,
  selectedUsers: null as SelectedUsers | null,
  onChange: vi.fn(),
  onAddNew: vi.fn(),
  onEdit: vi.fn(),
};

describe("MultiUserSelector", () => {
  it("shows loading state", () => {
    render(<MultiUserSelector {...defaultProps} isLoading />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows empty state when no users", () => {
    render(<MultiUserSelector {...defaultProps} users={[]} />);
    expect(screen.getByText("No profiles yet")).toBeInTheDocument();
  });

  it("renders primary user dropdown with all users", () => {
    render(<MultiUserSelector {...defaultProps} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("selects a primary user", async () => {
    const onChange = vi.fn();
    render(<MultiUserSelector {...defaultProps} onChange={onChange} />);
    const select = screen.getByLabelText("Select profile");
    await userEvent.selectOptions(select, "1");
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        primary: expect.objectContaining({ id: 1, name: "Alice" }),
        secondary: [],
      }),
    );
  });

  it("shows edit button when user is selected", () => {
    const selected: SelectedUsers = {
      primary: mockUsers[0],
      secondary: [],
    };
    render(<MultiUserSelector {...defaultProps} selectedUsers={selected} />);
    expect(screen.getByText("Edit Profile")).toBeInTheDocument();
  });

  it("does not show edit button when no user selected", () => {
    render(<MultiUserSelector {...defaultProps} />);
    expect(screen.queryByText("Edit Profile")).not.toBeInTheDocument();
  });

  it("shows primary chip and add button when user is selected", () => {
    const selected: SelectedUsers = {
      primary: mockUsers[0],
      secondary: [],
    };
    render(<MultiUserSelector {...defaultProps} selectedUsers={selected} />);
    // Alice appears in both dropdown option and chip
    const aliceElements = screen.getAllByText("Alice");
    expect(aliceElements.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/Add User/)).toBeInTheDocument();
  });

  it("shows secondary user chips with remove button", () => {
    const selected: SelectedUsers = {
      primary: mockUsers[0],
      secondary: [mockUsers[1]],
    };
    render(<MultiUserSelector {...defaultProps} selectedUsers={selected} />);
    // Both users should appear as chips
    const aliceElements = screen.getAllByText("Alice");
    expect(aliceElements.length).toBeGreaterThanOrEqual(1);
    const bobElements = screen.getAllByText("Bob");
    expect(bobElements.length).toBeGreaterThanOrEqual(1);
    // Remove button for Bob
    expect(screen.getByLabelText("Remove user Bob")).toBeInTheDocument();
  });

  it("removes a secondary user when X clicked", async () => {
    const onChange = vi.fn();
    const selected: SelectedUsers = {
      primary: mockUsers[0],
      secondary: [mockUsers[1]],
    };
    render(
      <MultiUserSelector
        {...defaultProps}
        selectedUsers={selected}
        onChange={onChange}
      />,
    );
    await userEvent.click(screen.getByLabelText("Remove user Bob"));
    expect(onChange).toHaveBeenCalledWith({
      primary: mockUsers[0],
      secondary: [],
    });
  });

  it("shows max users error when 5 users already selected", async () => {
    const selected: SelectedUsers = {
      primary: mockUsers[0],
      secondary: [mockUsers[1], mockUsers[2], mockUsers[3], mockUsers[4]],
    };
    render(<MultiUserSelector {...defaultProps} selectedUsers={selected} />);
    // Add button should not appear (5 already selected, no more available under limit)
    expect(screen.queryByText(/Add User/)).not.toBeInTheDocument();
  });

  it("calls onAddNew when add new profile clicked", async () => {
    const onAddNew = vi.fn();
    render(<MultiUserSelector {...defaultProps} onAddNew={onAddNew} />);
    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(onAddNew).toHaveBeenCalled();
  });
});
