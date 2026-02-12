import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReadingSection } from "../ReadingSection";

describe("ReadingSection", () => {
  it("renders title and children", () => {
    render(
      <ReadingSection title="Test Section">
        <p>Section content</p>
      </ReadingSection>,
    );
    expect(screen.getByText("Test Section")).toBeInTheDocument();
    expect(screen.getByText("Section content")).toBeInTheDocument();
  });

  it("collapses and expands on click", async () => {
    render(
      <ReadingSection title="Collapsible">
        <p>Hidden content</p>
      </ReadingSection>,
    );
    expect(screen.getByText("Hidden content")).toBeInTheDocument();
    await userEvent.click(screen.getByText("Collapsible"));
    expect(screen.queryByText("Hidden content")).not.toBeInTheDocument();
    await userEvent.click(screen.getByText("Collapsible"));
    expect(screen.getByText("Hidden content")).toBeInTheDocument();
  });

  it("applies priority border color", () => {
    const { container } = render(
      <ReadingSection title="Warning" priority="high">
        <p>Content</p>
      </ReadingSection>,
    );
    const section = container.querySelector("[data-reading-section]");
    expect(section?.className).toContain("border-nps-error");
  });
});
