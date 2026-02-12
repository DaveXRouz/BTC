import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReadingHeader } from "../ReadingHeader";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.type_reading": "Reading",
        "oracle.type_question": "Question",
        "oracle.type_name": "Name",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("ReadingHeader", () => {
  it("shows user name and formatted date", () => {
    render(
      <ReadingHeader
        userName="John Doe"
        readingDate="2024-01-15T12:00:00Z"
        readingType="reading"
      />,
    );
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Reading")).toBeInTheDocument();
    // Date is formatted by browser locale
    expect(screen.getByText(/2024/)).toBeInTheDocument();
  });

  it("shows confidence pill with correct color", () => {
    render(
      <ReadingHeader
        userName="Jane"
        readingDate="2024-01-15T12:00:00Z"
        readingType="reading"
        confidence={0.85}
      />,
    );
    const pill = screen.getByTestId("confidence-pill");
    expect(pill).toHaveTextContent("85%");
    expect(pill.className).toContain("bg-nps-success");
  });
});
