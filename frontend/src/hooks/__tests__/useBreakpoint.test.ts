import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useBreakpoint } from "../useBreakpoint";

type MatchMediaListener = (e: { matches: boolean }) => void;

function mockMatchMedia(width: number) {
  const listeners: Map<string, MatchMediaListener[]> = new Map();

  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });

  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn((query: string) => {
      // Parse "(min-width: Xpx)"
      const match = query.match(/min-width:\s*(\d+)px/);
      const breakpoint = match ? parseInt(match[1]) : 0;
      const matches = width >= breakpoint;

      if (!listeners.has(query)) {
        listeners.set(query, []);
      }

      return {
        matches,
        media: query,
        addEventListener: vi.fn((_: string, cb: MatchMediaListener) => {
          listeners.get(query)?.push(cb);
        }),
        removeEventListener: vi.fn((_: string, cb: MatchMediaListener) => {
          const arr = listeners.get(query);
          if (arr) {
            const idx = arr.indexOf(cb);
            if (idx >= 0) arr.splice(idx, 1);
          }
        }),
        dispatchEvent: vi.fn(),
      };
    }),
  });

  return listeners;
}

describe("useBreakpoint", () => {
  const originalInnerWidth = window.innerWidth;
  const originalMatchMedia = window.matchMedia;

  afterEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: originalMatchMedia,
    });
  });

  it("returns mobile when viewport < 640px", () => {
    mockMatchMedia(375);
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.breakpoint).toBe("mobile");
  });

  it("returns tablet when viewport 640-1023px", () => {
    mockMatchMedia(768);
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.breakpoint).toBe("tablet");
  });

  it("returns desktop when viewport >= 1024px", () => {
    mockMatchMedia(1440);
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(true);
    expect(result.current.breakpoint).toBe("desktop");
  });

  it("responds to resize events", () => {
    const listeners = mockMatchMedia(1440);
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.isDesktop).toBe(true);

    // Simulate resize to mobile
    act(() => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375,
      });

      // Trigger all registered listeners
      for (const [, cbs] of listeners) {
        for (const cb of cbs) {
          cb({ matches: false });
        }
      }
    });

    expect(result.current.isMobile).toBe(true);
    expect(result.current.isDesktop).toBe(false);
  });
});
