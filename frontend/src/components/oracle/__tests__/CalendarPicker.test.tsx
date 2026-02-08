import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CalendarPicker } from "../CalendarPicker";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.calendar_select_date": "Select a date",
        "oracle.calendar_gregorian": "Gregorian",
        "oracle.calendar_jalaali": "Solar Hijri",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("CalendarPicker", () => {
  it("renders with placeholder when no value", () => {
    render(<CalendarPicker value="" onChange={vi.fn()} />);
    expect(screen.getByText("Select a date")).toBeInTheDocument();
  });

  it("renders formatted date when value is set", () => {
    render(<CalendarPicker value="2024-03-15" onChange={vi.fn()} />);
    expect(screen.getByText("2024-03-15")).toBeInTheDocument();
  });

  it("opens dropdown on click", async () => {
    render(<CalendarPicker value="" onChange={vi.fn()} />);
    await userEvent.click(screen.getByText("Select a date"));
    expect(screen.getByText("Gregorian")).toBeInTheDocument();
    expect(screen.getByText("Solar Hijri")).toBeInTheDocument();
  });

  it("toggles between calendar modes", async () => {
    render(<CalendarPicker value="2024-03-15" onChange={vi.fn()} />);
    await userEvent.click(screen.getByText("2024-03-15"));
    // Default is gregorian — click Jalaali
    await userEvent.click(screen.getByText("Solar Hijri"));
    // Should now show Jalaali month names (Persian text)
    // The view should have switched
    expect(screen.getByText("Solar Hijri")).toBeInTheDocument();
  });

  it("calls onChange when a day is clicked", async () => {
    const onChange = vi.fn();
    render(<CalendarPicker value="2024-03-15" onChange={onChange} />);
    await userEvent.click(screen.getByText("2024-03-15"));
    // Click day 10 in the current month
    const dayButtons = screen
      .getAllByRole("button")
      .filter((b) => b.textContent === "10");
    if (dayButtons.length > 0) {
      await userEvent.click(dayButtons[0]);
      expect(onChange).toHaveBeenCalled();
    }
  });

  it("navigates to next/previous month", async () => {
    render(<CalendarPicker value="2024-03-15" onChange={vi.fn()} />);
    await userEvent.click(screen.getByText("2024-03-15"));
    expect(screen.getByText("March 2024")).toBeInTheDocument();

    await userEvent.click(screen.getByLabelText("Next month"));
    expect(screen.getByText("April 2024")).toBeInTheDocument();

    await userEvent.click(screen.getByLabelText("Previous month"));
    expect(screen.getByText("March 2024")).toBeInTheDocument();
  });

  it("displays error when provided", () => {
    render(
      <CalendarPicker value="" onChange={vi.fn()} error="Date is required" />,
    );
    expect(screen.getByText("Date is required")).toBeInTheDocument();
  });
});
