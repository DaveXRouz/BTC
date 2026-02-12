import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PersianKeyboard } from "../PersianKeyboard";

// Mock matchMedia for useBreakpoint (jsdom doesn't have it)
// Simulate desktop viewport so PersianKeyboard renders desktop version
beforeAll(() => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: 1440,
  });
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn((query: string) => {
      const match = query.match(/min-width:\s*(\d+)px/);
      const breakpoint = match ? parseInt(match[1]) : 0;
      return {
        matches: 1440 >= breakpoint,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };
    }),
  });
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.keyboard_persian": "Persian Keyboard",
        "oracle.keyboard_close": "Close keyboard",
        "oracle.keyboard_space": "Space",
        "oracle.keyboard_backspace": "Backspace",
        "oracle.keyboard_shift": "Shift",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("PersianKeyboard", () => {
  it("renders base Persian characters by default", () => {
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    // Base characters should be visible
    expect(screen.getByText("ض")).toBeInTheDocument();
    expect(screen.getByText("ش")).toBeInTheDocument();
    expect(screen.getByText("ظ")).toBeInTheDocument();
    expect(screen.getByText("ژ")).toBeInTheDocument();
  });

  it("shift toggles to numbers and symbols layer", async () => {
    const user = userEvent.setup();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    // Click Shift button
    await user.click(screen.getByLabelText("Shift"));

    // Shift layer characters should now be visible
    expect(screen.getByText("۱")).toBeInTheDocument();
    expect(screen.getByText("۲")).toBeInTheDocument();
    expect(screen.getByText("۰")).toBeInTheDocument();

    // Base characters should NOT be visible
    expect(screen.queryByText("ض")).not.toBeInTheDocument();
  });

  it("shift toggles back to base layer on second click", async () => {
    const user = userEvent.setup();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    // Click Shift twice
    await user.click(screen.getByLabelText("Shift"));
    await user.click(screen.getByLabelText("Shift"));

    // Base characters should be back
    expect(screen.getByText("ض")).toBeInTheDocument();
    expect(screen.queryByText("۱")).not.toBeInTheDocument();
  });

  it("calls onCharacterClick when a character is clicked", async () => {
    const onChar = vi.fn();
    const user = userEvent.setup();
    render(
      <PersianKeyboard
        onCharacterClick={onChar}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    await user.click(screen.getByText("ض"));
    expect(onChar).toHaveBeenCalledWith("ض");
  });

  it("touch event fires onCharacterClick for mobile", () => {
    const onChar = vi.fn();
    render(
      <PersianKeyboard
        onCharacterClick={onChar}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    const charButton = screen.getByLabelText("ض");
    fireEvent.touchStart(charButton);
    expect(onChar).toHaveBeenCalledWith("ض");
  });

  it("calls onBackspace when backspace is clicked", async () => {
    const onBackspace = vi.fn();
    const user = userEvent.setup();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={onBackspace}
        onClose={vi.fn()}
      />,
    );
    await user.click(screen.getByText("⌫"));
    expect(onBackspace).toHaveBeenCalled();
  });

  it("calls onClose when close button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={onClose}
      />,
    );
    await user.click(screen.getByLabelText("Close keyboard"));
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
    expect(screen.getByLabelText("ض")).toBeInTheDocument();
  });

  it("shift button has active styling when shifted", async () => {
    const user = userEvent.setup();
    render(
      <PersianKeyboard
        onCharacterClick={vi.fn()}
        onBackspace={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    const shiftBtn = screen.getByLabelText("Shift");
    await user.click(shiftBtn);
    expect(shiftBtn.className).toContain("bg-nps-oracle-accent/30");
  });
});
