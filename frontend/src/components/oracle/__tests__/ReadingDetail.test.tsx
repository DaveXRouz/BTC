import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { ReadingDetail } from "../ReadingDetail";
import type { StoredReading } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.toggle_favorite": "Toggle favorite",
        "oracle.delete_reading": "Delete",
        "oracle.close_detail": "Close",
        "oracle.question_label": "Question",
        "oracle.sign_label": "Sign",
        "oracle.ai_interpretation": "AI Interpretation",
        "oracle.reading_data": "Reading Data",
      };
      return map[key] ?? key;
    },
  }),
}));

const baseReading: StoredReading = {
  id: 42,
  user_id: 1,
  sign_type: "question",
  sign_value: "test-sign",
  question: "What is my future?",
  reading_result: { foo: "bar" },
  ai_interpretation: "The stars suggest...",
  created_at: "2024-03-10T15:30:00Z",
  is_favorite: true,
  deleted_at: null,
};

describe("ReadingDetail", () => {
  it("renders question and AI interpretation", () => {
    renderWithProviders(
      <ReadingDetail
        reading={baseReading}
        onClose={vi.fn()}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("What is my future?")).toBeInTheDocument();
    expect(screen.getByText("The stars suggest...")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", async () => {
    const onClose = vi.fn();
    renderWithProviders(
      <ReadingDetail
        reading={baseReading}
        onClose={onClose}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByText("Close"));
    expect(onClose).toHaveBeenCalled();
  });

  it("shows reading data as JSON", () => {
    renderWithProviders(
      <ReadingDetail
        reading={baseReading}
        onClose={vi.fn()}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText(/"foo": "bar"/)).toBeInTheDocument();
  });
});
