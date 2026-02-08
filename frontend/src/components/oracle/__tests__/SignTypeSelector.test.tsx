import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SignTypeSelector } from "../SignTypeSelector";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.sign_label": "Sign",
        "oracle.sign_type_label": "Sign type",
        "oracle.sign_type_time": "Time",
        "oracle.sign_type_number": "Number",
        "oracle.sign_type_carplate": "Car Plate",
        "oracle.sign_type_custom": "Custom",
        "oracle.sign_placeholder_number": "Enter a number",
        "oracle.sign_placeholder_carplate": "12A345-67",
        "oracle.sign_placeholder_custom": "Enter your sign",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("SignTypeSelector", () => {
  it("renders the type dropdown with all options", () => {
    render(
      <SignTypeSelector
        value={{ type: "time", value: "" }}
        onChange={vi.fn()}
      />,
    );
    const select = screen.getByLabelText("Sign type");
    expect(select).toBeInTheDocument();
    expect(screen.getByText("Time")).toBeInTheDocument();
    expect(screen.getByText("Number")).toBeInTheDocument();
    expect(screen.getByText("Car Plate")).toBeInTheDocument();
    expect(screen.getByText("Custom")).toBeInTheDocument();
  });

  it("shows time input when type is time", () => {
    render(
      <SignTypeSelector
        value={{ type: "time", value: "" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Time")).toBeInTheDocument();
  });

  it("shows number input when type is number", () => {
    render(
      <SignTypeSelector
        value={{ type: "number", value: "" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("Enter a number")).toBeInTheDocument();
  });

  it("shows carplate input when type is carplate", () => {
    render(
      <SignTypeSelector
        value={{ type: "carplate", value: "" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("12A345-67")).toBeInTheDocument();
  });

  it("resets value when type changes", async () => {
    const onChange = vi.fn();
    render(
      <SignTypeSelector
        value={{ type: "time", value: "12:00" }}
        onChange={onChange}
      />,
    );
    const select = screen.getByLabelText("Sign type");
    await userEvent.selectOptions(select, "number");
    expect(onChange).toHaveBeenCalledWith({ type: "number", value: "" });
  });

  it("displays error message when provided", () => {
    render(
      <SignTypeSelector
        value={{ type: "time", value: "" }}
        onChange={vi.fn()}
        error="Sign value is required"
      />,
    );
    expect(screen.getByText("Sign value is required")).toBeInTheDocument();
  });
});
