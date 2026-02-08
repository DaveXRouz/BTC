import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OracleConsultationForm } from "../OracleConsultationForm";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, string>) => {
      const map: Record<string, string> = {
        "oracle.consulting_for": `Consulting for ${params?.name ?? ""}`,
        "oracle.question_label": "Question",
        "oracle.question_placeholder": "Type your question here...",
        "oracle.date_label": "Date",
        "oracle.submit_reading": "Submit Reading",
        "oracle.keyboard_toggle": "Toggle Persian keyboard",
        "oracle.keyboard_persian": "Persian Keyboard",
        "oracle.keyboard_close": "Close keyboard",
        "oracle.keyboard_space": "Space",
        "oracle.keyboard_backspace": "Backspace",
        "oracle.calendar_select_date": "Select a date",
        "oracle.calendar_gregorian": "Gregorian",
        "oracle.calendar_jalaali": "Solar Hijri",
        "oracle.sign_label": "Sign",
        "oracle.sign_type_label": "Sign type",
        "oracle.sign_type_time": "Time",
        "oracle.sign_type_number": "Number",
        "oracle.sign_type_carplate": "Car Plate",
        "oracle.sign_type_custom": "Custom",
        "oracle.sign_placeholder_number": "Enter a number",
        "oracle.sign_placeholder_carplate": "12A345-67",
        "oracle.sign_placeholder_custom": "Enter your sign",
        "oracle.location_label": "Location",
        "oracle.location_auto_detect": "Auto-Detect Location",
        "oracle.location_detecting": "Detecting...",
        "oracle.location_detect_error":
          "Could not detect location. Please select manually.",
        "oracle.location_country": "Country",
        "oracle.location_city": "City",
        "oracle.location_coordinates": "Coordinates",
        "oracle.error_sign_required": "Sign value is required",
        "oracle.error_time_format": "Invalid time format (HH:MM)",
        "common.loading": "Loading...",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("OracleConsultationForm", () => {
  it("renders all form fields", () => {
    render(<OracleConsultationForm userId={1} userName="Alice" />);
    expect(screen.getByText("Consulting for Alice")).toBeInTheDocument();
    expect(screen.getByText("Question")).toBeInTheDocument();
    expect(screen.getByText("Sign")).toBeInTheDocument();
    expect(screen.getByText("Location")).toBeInTheDocument();
    expect(screen.getByText("Submit Reading")).toBeInTheDocument();
  });

  it("toggles Persian keyboard on icon click", async () => {
    render(<OracleConsultationForm userId={1} userName="Alice" />);
    const toggleBtn = screen.getByLabelText("Toggle Persian keyboard");
    await userEvent.click(toggleBtn);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    // Click close
    await userEvent.click(screen.getByLabelText("Close keyboard"));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("types via Persian keyboard into question field", async () => {
    render(<OracleConsultationForm userId={1} userName="Alice" />);
    // Open keyboard
    await userEvent.click(screen.getByLabelText("Toggle Persian keyboard"));
    // Click a character
    await userEvent.click(screen.getByLabelText("ض"));
    const textarea = screen.getByPlaceholderText("Type your question here...");
    expect(textarea).toHaveValue("ض");
  });

  it("shows submit button", () => {
    render(<OracleConsultationForm userId={1} userName="Alice" />);
    expect(screen.getByText("Submit Reading")).toBeInTheDocument();
  });

  it("shows sign validation error on submit with empty sign", async () => {
    render(<OracleConsultationForm userId={1} userName="Alice" />);
    await userEvent.click(screen.getByText("Submit Reading"));
    expect(screen.getByText("Sign value is required")).toBeInTheDocument();
  });
});
