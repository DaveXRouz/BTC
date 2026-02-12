import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "../EmptyState";

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });

  it("renders title and description", () => {
    render(
      <EmptyState title="Empty" description="Try adding something new." />,
    );
    expect(screen.getByText("Empty")).toBeInTheDocument();
    expect(screen.getByText("Try adding something new.")).toBeInTheDocument();
  });

  it("renders icon variant", () => {
    const { container } = render(<EmptyState icon="vault" title="No data" />);
    // Should have an icon element
    const icon = container.querySelector('[role="img"]');
    expect(icon).toBeInTheDocument();
  });

  it("action button calls onClick", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    render(
      <EmptyState
        title="Empty"
        action={{ label: "Add Item", onClick: handler }}
      />,
    );
    await user.click(screen.getByText("Add Item"));
    expect(handler).toHaveBeenCalledOnce();
  });

  it("no action button when prop omitted", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders all 6 icon variants without error", () => {
    const variants = [
      "readings",
      "profiles",
      "vault",
      "search",
      "learning",
      "generic",
    ] as const;
    for (const icon of variants) {
      const { unmount } = render(
        <EmptyState icon={icon} title={`${icon} state`} />,
      );
      expect(screen.getByText(`${icon} state`)).toBeInTheDocument();
      unmount();
    }
  });
});
