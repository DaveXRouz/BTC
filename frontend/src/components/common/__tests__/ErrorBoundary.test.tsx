import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import i18n from "@/i18n/config";
import { ErrorBoundary } from "../ErrorBoundary";

// Suppress React error boundary console.error noise in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    const msg = typeof args[0] === "string" ? args[0] : "";
    if (msg.includes("ErrorBoundary") || msg.includes("The above error"))
      return;
    originalError.call(console, ...args);
  };
});
afterAll(() => {
  console.error = originalError;
});

function ThrowingComponent({ shouldThrow = true }: { shouldThrow?: boolean }) {
  if (shouldThrow) throw new Error("Test error");
  return <div>All good</div>;
}

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("ErrorBoundary", () => {
  it("renders children when no error", () => {
    renderWithI18n(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("shows fallback when child throws during render", () => {
    renderWithI18n(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("Try Again button resets and re-renders children", async () => {
    const user = userEvent.setup();
    let shouldThrow = true;

    function ConditionalThrower() {
      if (shouldThrow) throw new Error("Oops");
      return <div>Recovered</div>;
    }

    renderWithI18n(
      <ErrorBoundary>
        <ConditionalThrower />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Fix the error condition before clicking retry
    shouldThrow = false;
    await user.click(screen.getByText("Try Again"));

    expect(screen.getByText("Recovered")).toBeInTheDocument();
  });

  it("custom fallback prop is used when provided", () => {
    renderWithI18n(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <ThrowingComponent />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Custom fallback")).toBeInTheDocument();
  });

  it("has Go to Dashboard link", () => {
    renderWithI18n(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>,
    );
    const link = screen.getByText("Go to Dashboard");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/dashboard");
  });
});
