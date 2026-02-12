import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { ReadingCard } from "../ReadingCard";
import type { StoredReading } from "@/types";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.toggle_favorite": "Toggle favorite",
        "oracle.delete_reading": "Delete",
      };
      return map[key] ?? key;
    },
  }),
}));

const baseReading: StoredReading = {
  id: 1,
  user_id: null,
  sign_type: "time",
  sign_value: "12:30:00",
  question: null,
  reading_result: null,
  ai_interpretation: "Test interpretation",
  created_at: "2024-01-15T12:00:00Z",
  is_favorite: false,
  deleted_at: null,
};

describe("ReadingCard", () => {
  it("renders sign type badge and sign value", () => {
    renderWithProviders(
      <ReadingCard
        reading={baseReading}
        onSelect={vi.fn()}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("time")).toBeInTheDocument();
    expect(screen.getByText("12:30:00")).toBeInTheDocument();
  });

  it("shows filled star for favorites", () => {
    const favReading = { ...baseReading, is_favorite: true };
    renderWithProviders(
      <ReadingCard
        reading={favReading}
        onSelect={vi.fn()}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByTitle("Toggle favorite").textContent).toBe("\u2605");
  });

  it("calls onSelect when body clicked", async () => {
    const onSelect = vi.fn();
    renderWithProviders(
      <ReadingCard
        reading={baseReading}
        onSelect={onSelect}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByText("12:30:00"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onToggleFavorite when star clicked", async () => {
    const onFav = vi.fn();
    renderWithProviders(
      <ReadingCard
        reading={baseReading}
        onSelect={vi.fn()}
        onToggleFavorite={onFav}
        onDelete={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByTitle("Toggle favorite"));
    expect(onFav).toHaveBeenCalledWith(1);
  });
});
