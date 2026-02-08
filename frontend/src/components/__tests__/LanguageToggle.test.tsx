import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LanguageToggle } from "../LanguageToggle";

let mockLanguage = "en";
const mockChangeLanguage = vi.fn((lang: string) => {
  mockLanguage = lang;
  return Promise.resolve();
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      get language() {
        return mockLanguage;
      },
      changeLanguage: mockChangeLanguage,
    },
  }),
}));

beforeEach(() => {
  mockLanguage = "en";
  mockChangeLanguage.mockClear();
});

describe("LanguageToggle", () => {
  it("renders EN and FA labels", () => {
    render(<LanguageToggle />);
    expect(screen.getByText("EN")).toBeInTheDocument();
    expect(screen.getByText("FA")).toBeInTheDocument();
  });

  it("highlights EN when language is English", () => {
    render(<LanguageToggle />);
    const en = screen.getByText("EN");
    expect(en.className).toContain("text-nps-oracle-accent");
    expect(en.className).toContain("font-bold");
  });

  it("calls changeLanguage to fa when toggled from en", async () => {
    render(<LanguageToggle />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockChangeLanguage).toHaveBeenCalledWith("fa");
  });

  it("calls changeLanguage to en when toggled from fa", async () => {
    mockLanguage = "fa";
    render(<LanguageToggle />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockChangeLanguage).toHaveBeenCalledWith("en");
  });

  it("highlights FA when language is Persian", () => {
    mockLanguage = "fa";
    render(<LanguageToggle />);
    const fa = screen.getByText("FA");
    expect(fa.className).toContain("text-nps-oracle-accent");
    expect(fa.className).toContain("font-bold");
  });
});
