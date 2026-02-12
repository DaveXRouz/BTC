import type { ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface SlideInProps {
  children: ReactNode;
  from?: "left" | "right" | "top" | "bottom";
  delay?: number;
  className?: string;
}

function getAnimationClass(from: string, isRtl: boolean): string {
  switch (from) {
    case "left":
      return isRtl ? "nps-animate-slide-right" : "nps-animate-slide-left";
    case "right":
      return isRtl ? "nps-animate-slide-left" : "nps-animate-slide-right";
    case "top":
      return "nps-animate-slide-down";
    case "bottom":
      return "nps-animate-fade-in-up";
    default:
      return "nps-animate-slide-left";
  }
}

export function SlideIn({
  children,
  from = "left",
  delay = 0,
  className = "",
}: SlideInProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <div className={className}>{children}</div>;
  }

  const isRtl =
    typeof document !== "undefined" && document.documentElement.dir === "rtl";
  const animClass = getAnimationClass(from, isRtl);

  return (
    <div
      className={`nps-animate-initial ${animClass} ${className}`}
      style={delay > 0 ? { animationDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
