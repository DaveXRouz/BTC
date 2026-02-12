import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";

// Mock useReducedMotion before importing components
const mockUseReducedMotion = vi.fn(() => false);
vi.mock("@/hooks/useReducedMotion", () => ({
  useReducedMotion: () => mockUseReducedMotion(),
}));

import { FadeIn } from "@/components/common/FadeIn";
import { SlideIn } from "@/components/common/SlideIn";
import { CountUp } from "@/components/common/CountUp";
import { StaggerChildren } from "@/components/common/StaggerChildren";
import { LoadingOrb } from "@/components/common/LoadingOrb";
import { PageTransition } from "@/components/common/PageTransition";

describe("useReducedMotion", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("returns false by default", async () => {
    // We test this indirectly through FadeIn behavior
    const { container } = render(<FadeIn>Content</FadeIn>);
    expect(container.querySelector(".nps-animate-initial")).toBeTruthy();
  });

  it("skips animation when reduced motion preferred", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(<FadeIn>Content</FadeIn>);
    expect(container.querySelector(".nps-animate-initial")).toBeNull();
    expect(screen.getByText("Content")).toBeInTheDocument();
  });
});

describe("FadeIn", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("renders children", () => {
    render(<FadeIn>Hello</FadeIn>);
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("applies animation class", () => {
    const { container } = render(<FadeIn>Content</FadeIn>);
    const wrapper = container.firstElementChild;
    expect(wrapper?.classList.contains("nps-animate-fade-in-up")).toBe(true);
  });

  it("skips animation when reduced motion preferred", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(<FadeIn>Content</FadeIn>);
    const wrapper = container.firstElementChild;
    expect(wrapper?.classList.contains("nps-animate-fade-in-up")).toBe(false);
    expect(wrapper?.classList.contains("nps-animate-initial")).toBe(false);
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("applies delay via inline style", () => {
    const { container } = render(<FadeIn delay={200}>Content</FadeIn>);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper?.style.animationDelay).toBe("200ms");
  });

  it("renders as span when specified", () => {
    const { container } = render(<FadeIn as="span">Content</FadeIn>);
    expect(container.firstElementChild?.tagName).toBe("SPAN");
  });
});

describe("SlideIn", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("applies slide-left class for left direction", () => {
    const { container } = render(<SlideIn from="left">Content</SlideIn>);
    const wrapper = container.firstElementChild;
    expect(wrapper?.classList.contains("nps-animate-slide-left")).toBe(true);
  });

  it("applies slide-right class for right direction", () => {
    const { container } = render(<SlideIn from="right">Content</SlideIn>);
    const wrapper = container.firstElementChild;
    expect(wrapper?.classList.contains("nps-animate-slide-right")).toBe(true);
  });

  it("renders children without animation when reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(<SlideIn from="left">Slide content</SlideIn>);
    expect(screen.getByText("Slide content")).toBeInTheDocument();
  });
});

describe("CountUp", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows final value immediately when reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(<CountUp value={42} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders dash for non-finite values", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(<CountUp value={NaN} />);
    expect(screen.getByText("\u2014")).toBeInTheDocument();
  });

  it("renders with prefix and suffix", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(<CountUp value={100} prefix="$" suffix="%" />);
    expect(screen.getByText("$100%")).toBeInTheDocument();
  });
});

describe("StaggerChildren", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("renders all children", () => {
    render(
      <StaggerChildren>
        <div>A</div>
        <div>B</div>
        <div>C</div>
      </StaggerChildren>,
    );
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();
  });

  it("renders all children immediately when reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(
      <StaggerChildren>
        <div>A</div>
        <div>B</div>
      </StaggerChildren>,
    );
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
  });
});

describe("LoadingOrb", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("renders with label", () => {
    render(<LoadingOrb label="Loading..." />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("applies pulse animation class", () => {
    render(<LoadingOrb />);
    const orb = screen.getByTestId("loading-orb");
    expect(orb.classList.contains("nps-animate-orb-pulse")).toBe(true);
  });

  it("renders static orb when reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(<LoadingOrb />);
    const orb = screen.getByTestId("loading-orb");
    expect(orb.classList.contains("nps-animate-orb-pulse")).toBe(false);
  });

  it("has role=status for accessibility", () => {
    render(<LoadingOrb label="Working..." />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});

describe("PageTransition", () => {
  beforeEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("renders children", () => {
    render(<PageTransition locationKey="page-1">Page 1</PageTransition>);
    expect(screen.getByText("Page 1")).toBeInTheDocument();
  });

  it("applies animation class", () => {
    const { container } = render(
      <PageTransition locationKey="page-1">Page 1</PageTransition>,
    );
    expect(container.querySelector(".nps-animate-fade-in")).toBeTruthy();
  });

  it("re-animates on key change", () => {
    const { rerender, container } = render(
      <PageTransition locationKey="page-1">Page 1</PageTransition>,
    );
    rerender(<PageTransition locationKey="page-2">Page 2</PageTransition>);
    expect(screen.getByText("Page 2")).toBeInTheDocument();
    expect(container.querySelector(".nps-animate-fade-in")).toBeTruthy();
  });

  it("renders children directly when reduced motion", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(
      <PageTransition locationKey="page-1">Page 1</PageTransition>,
    );
    expect(container.querySelector(".nps-animate-fade-in")).toBeNull();
    expect(screen.getByText("Page 1")).toBeInTheDocument();
  });
});
