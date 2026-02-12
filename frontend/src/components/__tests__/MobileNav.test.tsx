import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { MobileNav } from "../MobileNav";

// Mock i18next
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: { language: "en", changeLanguage: vi.fn() },
    }),
  };
});

// Mock useDirection
vi.mock("@/hooks/useDirection", () => ({
  useDirection: () => ({ dir: "ltr", isRTL: false, locale: "en" }),
}));

// Mock ThemeToggle
vi.mock("../ThemeToggle", () => ({
  ThemeToggle: () => <button data-testid="theme-toggle">Theme</button>,
}));

// Mock useWebSocket
vi.mock("@/hooks/useWebSocket", () => ({
  useWebSocketConnection: () => undefined,
}));

function renderMobileNav(isOpen: boolean, onClose = vi.fn()) {
  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <MobileNav isOpen={isOpen} onClose={onClose} />
    </MemoryRouter>,
  );
}

describe("MobileNav", () => {
  it("renders drawer as dialog when open", () => {
    renderMobileNav(true);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeDefined();
  });

  it("shows all nav items", () => {
    renderMobileNav(true);
    expect(screen.getByText("nav.dashboard")).toBeDefined();
    expect(screen.getByText("nav.oracle")).toBeDefined();
    expect(screen.getByText("nav.history")).toBeDefined();
    expect(screen.getByText("nav.settings")).toBeDefined();
    expect(screen.getByText("nav.scanner")).toBeDefined();
  });

  it("closes on Escape key", () => {
    const onClose = vi.fn();
    renderMobileNav(true, onClose);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("closes on backdrop click", () => {
    const onClose = vi.fn();
    const { container } = renderMobileNav(true, onClose);
    // The first child of the rendered output should be the backdrop
    const backdrop = container.querySelector("[aria-hidden='true']");
    expect(backdrop).toBeDefined();
    if (backdrop) fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("closes on nav item click", () => {
    const onClose = vi.fn();
    renderMobileNav(true, onClose);
    const dashboardLink = screen.getByText("nav.dashboard");
    fireEvent.click(dashboardLink);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("has close button", () => {
    const onClose = vi.fn();
    renderMobileNav(true, onClose);
    const closeButton = screen.getByLabelText("layout.mobile_menu_close");
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalledOnce();
  });
});
