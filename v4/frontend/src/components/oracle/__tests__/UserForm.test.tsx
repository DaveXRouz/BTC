import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserForm } from "../UserForm";
import type { OracleUser } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "common.loading": "Loading...",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "oracle.new_profile": "New Profile",
        "oracle.edit_profile": "Edit Profile",
        "oracle.add_new_profile": "Add New Profile",
        "oracle.delete_profile": "Delete",
        "oracle.delete_confirm": "Confirm Delete",
        "oracle.field_name": "Name",
        "oracle.field_name_persian": "Name (Persian)",
        "oracle.field_birthday": "Birthday",
        "oracle.field_mother_name": "Mother's Name",
        "oracle.field_mother_name_persian": "Mother's Name (Persian)",
        "oracle.field_country": "Country",
        "oracle.field_city": "City",
        "oracle.error_name_required": "Name must be at least 2 characters",
        "oracle.error_birthday_required": "Birthday is required",
        "oracle.error_birthday_future": "Birthday cannot be in the future",
        "oracle.error_mother_name_required":
          "Mother's name must be at least 2 characters",
      };
      return map[key] ?? key;
    },
  }),
}));

const existingUser: OracleUser = {
  id: 1,
  name: "Alice",
  name_persian: "آلیس",
  birthday: "1990-01-15",
  mother_name: "Carol",
  mother_name_persian: "کارول",
  country: "US",
  city: "NYC",
  created_at: "2024-01-01T00:00:00Z",
};

describe("UserForm", () => {
  it("renders in create mode with empty fields", () => {
    render(<UserForm onSubmit={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByText("New Profile")).toBeInTheDocument();
    expect(screen.getByText(/Add New Profile/)).toBeInTheDocument();
  });

  it("renders in edit mode with pre-populated fields", () => {
    render(
      <UserForm
        user={existingUser}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("Edit Profile")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Alice")).toBeInTheDocument();
    expect(screen.getByDisplayValue("1990-01-15")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Carol")).toBeInTheDocument();
  });

  it("shows validation errors for empty required fields", async () => {
    const onSubmit = vi.fn();
    render(<UserForm onSubmit={onSubmit} onCancel={vi.fn()} />);
    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(
      screen.getByText("Name must be at least 2 characters"),
    ).toBeInTheDocument();
    expect(screen.getByText("Birthday is required")).toBeInTheDocument();
    expect(
      screen.getByText("Mother's name must be at least 2 characters"),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error for future birthday", async () => {
    render(<UserForm onSubmit={vi.fn()} onCancel={vi.fn()} />);
    const inputs = screen.getAllByRole("textbox");
    await userEvent.type(inputs[0], "Test User");

    // Fill birthday with future date
    const allInputs = document.querySelectorAll("input");
    const birthdayInput = Array.from(allInputs).find((i) => i.type === "date")!;
    await userEvent.type(birthdayInput, "2099-01-01");

    // Fill mother's name
    await userEvent.type(inputs[2], "Mother Test");

    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(
      screen.getByText("Birthday cannot be in the future"),
    ).toBeInTheDocument();
  });

  it("calls onSubmit with form data on valid submission", async () => {
    const onSubmit = vi.fn();
    render(<UserForm onSubmit={onSubmit} onCancel={vi.fn()} />);
    const inputs = screen.getAllByRole("textbox");
    await userEvent.type(inputs[0], "Test User");

    const allInputs = document.querySelectorAll("input");
    const birthdayInput = Array.from(allInputs).find((i) => i.type === "date")!;
    await userEvent.type(birthdayInput, "1990-05-15");

    await userEvent.type(inputs[2], "Mother Test");

    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Test User",
        birthday: "1990-05-15",
        mother_name: "Mother Test",
      }),
    );
  });

  it("calls onCancel when cancel button clicked", async () => {
    const onCancel = vi.fn();
    render(<UserForm onSubmit={vi.fn()} onCancel={onCancel} />);
    await userEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalled();
  });

  it("calls onCancel when backdrop clicked", async () => {
    const onCancel = vi.fn();
    const { container } = render(
      <UserForm onSubmit={vi.fn()} onCancel={onCancel} />,
    );
    // Click the backdrop (outermost div with fixed positioning)
    const backdrop = container.querySelector(".fixed")!;
    await userEvent.click(backdrop);
    expect(onCancel).toHaveBeenCalled();
  });

  it("shows delete button only in edit mode", () => {
    const { rerender } = render(
      <UserForm onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(screen.queryByText("Delete")).not.toBeInTheDocument();

    rerender(
      <UserForm
        user={existingUser}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });

  it("requires two clicks to delete", async () => {
    const onDelete = vi.fn();
    render(
      <UserForm
        user={existingUser}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        onDelete={onDelete}
      />,
    );
    const deleteBtn = screen.getByText("Delete");
    await userEvent.click(deleteBtn);
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByText("Confirm Delete")).toBeInTheDocument();

    await userEvent.click(screen.getByText("Confirm Delete"));
    expect(onDelete).toHaveBeenCalled();
  });

  it("renders Persian fields with RTL direction", () => {
    render(
      <UserForm user={existingUser} onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );
    const persianInput = screen.getByDisplayValue("آلیس");
    expect(persianInput).toHaveAttribute("dir", "rtl");
  });

  it("clears validation error on field change", async () => {
    render(<UserForm onSubmit={vi.fn()} onCancel={vi.fn()} />);
    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(
      screen.getByText("Name must be at least 2 characters"),
    ).toBeInTheDocument();

    const inputs = screen.getAllByRole("textbox");
    await userEvent.type(inputs[0], "Te");
    expect(
      screen.queryByText("Name must be at least 2 characters"),
    ).not.toBeInTheDocument();
  });

  it("disables submit button when isSubmitting is true", () => {
    render(<UserForm onSubmit={vi.fn()} onCancel={vi.fn()} isSubmitting />);
    const submitBtn = screen.getByText("Loading...");
    expect(submitBtn).toBeDisabled();
  });
});
