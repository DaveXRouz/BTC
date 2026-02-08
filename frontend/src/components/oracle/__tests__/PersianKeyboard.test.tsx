import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PersianKeyboard } from "../PersianKeyboard";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.keyboard_persian": "Persian Keyboard",
        "oracle.keyboard_close": "Close keyboard",
        "oracle.keyboard_space": "Space",
        "oracle.keyboard_backspace": "Backspace",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("PersianKeyboard", () => {
  it("renders all character rows", () => {
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    // Check some Persian characters are rendered
    expect(screen.getByText("ض")).toBeInTheDocument();
    expect(screen.getByText("ش")).toBeInTheDocument();
    expect(screen.getByText("ظ")).toBeInTheDocument();
    expect(screen.getByText("ژ")).toBeInTheDocument();
  });

  it("calls onCharacterClick when a character is clicked", async () => {
    const onChar = vi.fn();
    render(
      <PersianKeyboard
        onCharacterClick={onChar}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByText("ض"));
    expect(onChar).toHaveBeenCalledWith("ض");
  });

  it("calls onBackspace when backspace is clicked", async () => {
    const onBackspace = vi.fn();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={onBackspace}
        onClose={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByText("⌫"));
    expect(onBackspace).toHaveBeenCalled();
  });

  it("calls onClose when close button is clicked", async () => {
    const onClose = vi.fn();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={onClose}
      />,
    );
    await userEvent.click(screen.getByLabelText("Close keyboard"));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={onClose}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("has correct ARIA attributes", () => {
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByRole("dialog")).toHaveAttribute(
      "aria-label",
      "Persian Keyboard",
    );
    // Each character button has an aria-label
    expect(screen.getByLabelText("ض")).toBeInTheDocument();
  });
});
