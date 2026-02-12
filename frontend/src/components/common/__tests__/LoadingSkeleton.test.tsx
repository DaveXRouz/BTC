import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingSkeleton } from "../LoadingSkeleton";

describe("LoadingSkeleton", () => {
  it("renders line variant", () => {
    render(<LoadingSkeleton variant="line" />);
    expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
  });

  it("renders card variant", () => {
    render(<LoadingSkeleton variant="card" />);
    expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
  });

  it("renders circle variant", () => {
    render(<LoadingSkeleton variant="circle" />);
    expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
  });

  it("renders grid variant with 4 cards", () => {
    const { container } = render(<LoadingSkeleton variant="grid" />);
    // Grid should have 4 card-like children
    const cards = container.querySelectorAll(".rounded-lg");
    expect(cards.length).toBeGreaterThanOrEqual(4);
  });

  it("renders list variant with multiple bars", () => {
    const { container } = render(<LoadingSkeleton variant="list" />);
    const bars = container.querySelectorAll(".h-4");
    expect(bars.length).toBeGreaterThanOrEqual(3);
  });

  it("renders reading variant (circle + lines + card)", () => {
    const { container } = render(<LoadingSkeleton variant="reading" />);
    const circles = container.querySelectorAll(".rounded-full");
    expect(circles.length).toBeGreaterThanOrEqual(1);
  });

  it("count renders multiple items", () => {
    const { container } = render(<LoadingSkeleton variant="card" count={3} />);
    const cards = container.querySelectorAll(".rounded-lg");
    expect(cards.length).toBe(3);
  });

  it("has shimmer animation class", () => {
    const { container } = render(<LoadingSkeleton variant="line" />);
    const shimmer = container.querySelector(".animate-shimmer");
    expect(shimmer).toBeInTheDocument();
  });

  it("has aria-hidden and sr-only text", () => {
    render(<LoadingSkeleton variant="line" />);
    const skeleton = screen.getByTestId("loading-skeleton");
    expect(skeleton).toHaveAttribute("aria-hidden", "true");
    expect(screen.getByText("Loading")).toHaveClass("sr-only");
  });
});
