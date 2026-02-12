import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { NumerologyNumberDisplay } from "../NumerologyNumberDisplay";
import { toPersianDigits } from "@/utils/persianDigits";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en" },
  }),
}));

describe("NumerologyNumberDisplay", () => {
  it("renders number, label, and meaning", () => {
    render(
      <NumerologyNumberDisplay
        number={7}
        label="Life Path"
        meaning="The Seeker"
      />,
    );
    expect(screen.getByTestId("numerology-number")).toHaveTextContent("7");
    expect(screen.getByText("Life Path")).toBeInTheDocument();
    expect(screen.getByText("The Seeker")).toBeInTheDocument();
  });

  it("converts to Persian digits via toPersianDigits utility", () => {
    expect(toPersianDigits(7)).toBe("\u06F7");
    expect(toPersianDigits(123)).toBe("\u06F1\u06F2\u06F3");
    expect(toPersianDigits(0)).toBe("\u06F0");
  });

  it("highlights master numbers (11, 22, 33)", () => {
    render(
      <NumerologyNumberDisplay number={11} label="Expression" meaning="" />,
    );
    expect(screen.getByTestId("master-badge")).toBeInTheDocument();
    expect(screen.getByTestId("master-badge")).toHaveTextContent(
      "Master Number",
    );
  });
});
