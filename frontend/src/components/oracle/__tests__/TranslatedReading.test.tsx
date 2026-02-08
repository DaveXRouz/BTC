import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TranslatedReading } from "../TranslatedReading";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.translate": "Translate to Persian",
        "oracle.translating": "Translating...",
        "oracle.translate_error": "Translation failed. Please try again.",
        "oracle.show_original": "Show original",
        "oracle.show_translation": "Show translation",
      };
      return map[key] ?? key;
    },
  }),
}));

const mockTranslate = vi.fn();

vi.mock("@/services/api", () => ({
  translation: {
    get translate() {
      return mockTranslate;
    },
  },
}));

beforeEach(() => {
  mockTranslate.mockReset();
});

describe("TranslatedReading", () => {
  it("shows the reading text", () => {
    render(<TranslatedReading reading="Your energy is strong today." />);
    expect(
      screen.getByText("Your energy is strong today."),
    ).toBeInTheDocument();
  });

  it("shows translate button", () => {
    render(<TranslatedReading reading="Hello world" />);
    expect(screen.getByText("Translate to Persian")).toBeInTheDocument();
  });

  it("shows loading state when translating", async () => {
    mockTranslate.mockReturnValue(new Promise(() => {})); // never resolves
    render(<TranslatedReading reading="Hello" />);
    await userEvent.click(screen.getByText("Translate to Persian"));
    expect(screen.getByText("Translating...")).toBeInTheDocument();
  });

  it("displays translated text after successful translation", async () => {
    mockTranslate.mockResolvedValue({
      source_text: "Hello",
      translated_text: "\u0633\u0644\u0627\u0645",
      source_lang: "en",
      target_lang: "fa",
      preserved_terms: [],
      ai_generated: false,
      elapsed_ms: 50,
      cached: false,
    });
    render(<TranslatedReading reading="Hello" />);
    await userEvent.click(screen.getByText("Translate to Persian"));
    await waitFor(() => {
      expect(screen.getByText("\u0633\u0644\u0627\u0645")).toBeInTheDocument();
    });
  });

  it("shows toggle button after translation", async () => {
    mockTranslate.mockResolvedValue({
      source_text: "Hello",
      translated_text: "\u0633\u0644\u0627\u0645",
      source_lang: "en",
      target_lang: "fa",
      preserved_terms: [],
      ai_generated: false,
      elapsed_ms: 50,
      cached: false,
    });
    render(<TranslatedReading reading="Hello" />);
    await userEvent.click(screen.getByText("Translate to Persian"));
    await waitFor(() => {
      expect(screen.getByText("Show original")).toBeInTheDocument();
    });
  });

  it("toggles between original and translation", async () => {
    mockTranslate.mockResolvedValue({
      source_text: "Hello",
      translated_text: "\u0633\u0644\u0627\u0645",
      source_lang: "en",
      target_lang: "fa",
      preserved_terms: [],
      ai_generated: false,
      elapsed_ms: 50,
      cached: false,
    });
    render(<TranslatedReading reading="Hello" />);
    await userEvent.click(screen.getByText("Translate to Persian"));
    await waitFor(() => {
      expect(screen.getByText("\u0633\u0644\u0627\u0645")).toBeInTheDocument();
    });

    // Toggle to original
    await userEvent.click(screen.getByText("Show original"));
    expect(screen.getByText("Hello")).toBeInTheDocument();

    // Toggle back to translation
    await userEvent.click(screen.getByText("Show translation"));
    expect(screen.getByText("\u0633\u0644\u0627\u0645")).toBeInTheDocument();
  });

  it("shows error message on translation failure", async () => {
    mockTranslate.mockRejectedValue(new Error("Network error"));
    render(<TranslatedReading reading="Hello" />);
    await userEvent.click(screen.getByText("Translate to Persian"));
    await waitFor(() => {
      expect(
        screen.getByText("Translation failed. Please try again."),
      ).toBeInTheDocument();
    });
  });
});
