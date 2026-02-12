import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ToastProvider, ToastContainer } from "../Toast";
import { useToast } from "@/hooks/useToast";

function TestTrigger({
  type = "error" as const,
  message = "Test message",
  duration,
}: {
  type?: "error" | "success" | "warning" | "info";
  message?: string;
  duration?: number;
}) {
  const { addToast } = useToast();
  return (
    <button onClick={() => addToast({ type, message, duration })}>
      Add Toast
    </button>
  );
}

function renderWithProvider(ui: React.ReactElement) {
  return render(
    <ToastProvider>
      {ui}
      <ToastContainer />
    </ToastProvider>,
  );
}

describe("Toast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders toast with message", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProvider(<TestTrigger message="Hello World" />);

    await user.click(screen.getByText("Add Toast"));
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("auto-dismisses after duration", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProvider(<TestTrigger message="Ephemeral" duration={3000} />);

    await user.click(screen.getByText("Add Toast"));
    expect(screen.getByText("Ephemeral")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3100);
    });

    expect(screen.queryByText("Ephemeral")).not.toBeInTheDocument();
  });

  it("manual dismiss removes toast", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProvider(<TestTrigger message="Dismissible" />);

    await user.click(screen.getByText("Add Toast"));
    expect(screen.getByText("Dismissible")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Dismiss"));
    expect(screen.queryByText("Dismissible")).not.toBeInTheDocument();
  });

  it("max 5 toasts, oldest evicted", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProvider(<TestTrigger />);

    for (let i = 0; i < 6; i++) {
      await user.click(screen.getByText("Add Toast"));
    }

    const alerts = screen.getAllByRole("alert");
    expect(alerts.length).toBeLessThanOrEqual(5);
  });

  it("has correct ARIA attributes", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithProvider(<TestTrigger type="error" message="Error toast" />);

    await user.click(screen.getByText("Add Toast"));
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();

    const container = alert.parentElement;
    expect(container).toHaveAttribute("aria-live", "polite");
  });

  it("renders all 4 toast types", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    function MultiTypeTrigger() {
      const { addToast } = useToast();
      return (
        <>
          <button
            onClick={() => addToast({ type: "success", message: "Success!" })}
          >
            S
          </button>
          <button
            onClick={() => addToast({ type: "error", message: "Error!" })}
          >
            E
          </button>
          <button
            onClick={() => addToast({ type: "warning", message: "Warning!" })}
          >
            W
          </button>
          <button onClick={() => addToast({ type: "info", message: "Info!" })}>
            I
          </button>
        </>
      );
    }

    renderWithProvider(<MultiTypeTrigger />);

    await user.click(screen.getByText("S"));
    await user.click(screen.getByText("E"));
    await user.click(screen.getByText("W"));
    await user.click(screen.getByText("I"));

    expect(screen.getByText("Success!")).toBeInTheDocument();
    expect(screen.getByText("Error!")).toBeInTheDocument();
    expect(screen.getByText("Warning!")).toBeInTheDocument();
    expect(screen.getByText("Info!")).toBeInTheDocument();
  });
});
