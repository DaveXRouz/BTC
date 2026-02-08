import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReadingResults } from "../ReadingResults";
import { UserForm } from "../UserForm";

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.tab_summary": "Summary",
        "oracle.tab_details": "Details",
        "oracle.tab_history": "History",
        "oracle.new_profile": "New Profile",
        "oracle.edit_profile": "Edit Profile",
        "oracle.field_name": "Name",
        "oracle.field_name_persian": "Persian Name",
        "oracle.field_birthday": "Birthday",
        "oracle.field_mother_name": "Mother Name",
        "oracle.field_mother_name_persian": "Mother Persian Name",
        "oracle.field_country": "Country",
        "oracle.field_city": "City",
        "oracle.error_name_required": "Name is required",
        "oracle.error_birthday_required": "Birthday is required",
        "oracle.error_mother_name_required": "Mother name is required",
        "oracle.error_birthday_future": "Birthday cannot be in the future",
        "oracle.add_new_profile": "Add Profile",
        "oracle.delete_profile": "Delete",
        "oracle.delete_confirm": "Confirm Delete",
        "common.loading": "Loading...",
        "common.save": "Save",
        "common.cancel": "Cancel",
      };
      return map[key] || key;
    },
    i18n: { language: "en" },
  }),
}));

// Mock child components
vi.mock("../SummaryTab", () => ({
  SummaryTab: () => <div data-testid="summary-tab">Summary Content</div>,
}));
vi.mock("../DetailsTab", () => ({
  DetailsTab: () => <div data-testid="details-tab">Details Content</div>,
}));
vi.mock("../ReadingHistory", () => ({
  ReadingHistory: () => <div data-testid="history-tab">History Content</div>,
}));
vi.mock("../ExportButton", () => ({
  ExportButton: () => <button>Export</button>,
}));

describe("ReadingResults Accessibility", () => {
  it("renders tablist with correct ARIA roles", () => {
    render(<ReadingResults result={null} />);
    expect(screen.getByRole("tablist")).toBeDefined();
  });

  it("renders tabs with role=tab", () => {
    render(<ReadingResults result={null} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(3);
  });

  it("marks active tab with aria-selected=true", () => {
    render(<ReadingResults result={null} />);
    const summaryTab = screen.getByRole("tab", { name: "Summary" });
    expect(summaryTab.getAttribute("aria-selected")).toBe("true");

    const detailsTab = screen.getByRole("tab", { name: "Details" });
    expect(detailsTab.getAttribute("aria-selected")).toBe("false");
  });

  it("has tabpanel for each tab with aria-labelledby", () => {
    render(<ReadingResults result={null} />);
    const panels = screen.getAllByRole("tabpanel");
    expect(panels).toHaveLength(3);

    expect(panels[0].getAttribute("aria-labelledby")).toBe("tab-summary");
    expect(panels[1].getAttribute("aria-labelledby")).toBe("tab-details");
    expect(panels[2].getAttribute("aria-labelledby")).toBe("tab-history");
  });

  it("tabs have aria-controls pointing to panels", () => {
    render(<ReadingResults result={null} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0].getAttribute("aria-controls")).toBe("tabpanel-summary");
    expect(tabs[1].getAttribute("aria-controls")).toBe("tabpanel-details");
    expect(tabs[2].getAttribute("aria-controls")).toBe("tabpanel-history");
  });
});

describe("UserForm Accessibility", () => {
  it("renders as a dialog with aria-modal", () => {
    render(<UserForm onSubmit={() => {}} onCancel={() => {}} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeDefined();
    expect(dialog.getAttribute("aria-modal")).toBe("true");
  });

  it("form inputs have aria-required for required fields", () => {
    render(<UserForm onSubmit={() => {}} onCancel={() => {}} />);
    // Name, Birthday, Mother Name should be required
    const nameInput = screen.getByLabelText(/Name/);
    expect(nameInput.getAttribute("aria-required")).toBe("true");
  });

  it("shows validation errors with role=alert", async () => {
    render(<UserForm onSubmit={() => {}} onCancel={() => {}} />);

    // Submit empty form
    const submitButton = screen.getByText("Add Profile");
    await userEvent.click(submitButton);

    // Error messages should appear with role=alert
    const alerts = screen.getAllByRole("alert");
    expect(alerts.length).toBeGreaterThan(0);
  });

  it("error messages linked via aria-describedby", async () => {
    render(<UserForm onSubmit={() => {}} onCancel={() => {}} />);

    const submitButton = screen.getByText("Add Profile");
    await userEvent.click(submitButton);

    // At least one input should have aria-invalid=true
    const invalidInputs = document.querySelectorAll('[aria-invalid="true"]');
    expect(invalidInputs.length).toBeGreaterThan(0);

    // Each invalid input should have aria-describedby
    invalidInputs.forEach((input) => {
      const describedBy = input.getAttribute("aria-describedby");
      expect(describedBy).toBeTruthy();
      // The referenced element should exist
      const errorEl = document.getElementById(describedBy!);
      expect(errorEl).toBeTruthy();
    });
  });
});
