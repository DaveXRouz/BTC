import { useState, useEffect } from "react";

interface BreakpointState {
  isMobile: boolean; // < 640px
  isTablet: boolean; // 640-1023px
  isDesktop: boolean; // >= 1024px
  breakpoint: "mobile" | "tablet" | "desktop";
}

function getBreakpoint(): BreakpointState {
  if (typeof window === "undefined") {
    return {
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      breakpoint: "desktop",
    };
  }

  const width = window.innerWidth;
  if (width < 640) {
    return {
      isMobile: true,
      isTablet: false,
      isDesktop: false,
      breakpoint: "mobile",
    };
  }
  if (width < 1024) {
    return {
      isMobile: false,
      isTablet: true,
      isDesktop: false,
      breakpoint: "tablet",
    };
  }
  return {
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    breakpoint: "desktop",
  };
}

export function useBreakpoint(): BreakpointState {
  const [state, setState] = useState<BreakpointState>(getBreakpoint);

  useEffect(() => {
    const smQuery = window.matchMedia("(min-width: 640px)");
    const lgQuery = window.matchMedia("(min-width: 1024px)");

    function update() {
      setState(getBreakpoint());
    }

    smQuery.addEventListener("change", update);
    lgQuery.addEventListener("change", update);

    return () => {
      smQuery.removeEventListener("change", update);
      lgQuery.removeEventListener("change", update);
    };
  }, []);

  return state;
}
