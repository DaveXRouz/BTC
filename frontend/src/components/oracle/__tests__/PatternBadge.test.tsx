import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PatternBadge } from "../PatternBadge";

describe("PatternBadge", () => {
  it("renders pattern text", () => {
    render(<PatternBadge pattern="Angel 111" priority="high" />);
    expect(screen.getByText("Angel 111")).toBeInTheDocument();
  });

  it("applies correct color class per priority", () => {
    const { rerender } = render(
      <PatternBadge pattern="High" priority="high" />,
    );
    expect(screen.getByText("High").className).toContain("text-nps-error");

    rerender(<PatternBadge pattern="Medium" priority="medium" />);
    expect(screen.getByText("Medium").className).toContain("text-nps-warning");

    rerender(<PatternBadge pattern="Low" priority="low" />);
    expect(screen.getByText("Low").className).toContain("text-nps-success");
  });
});
