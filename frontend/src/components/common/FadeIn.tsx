import type { ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface FadeInProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  direction?: "up" | "down" | "none";
  className?: string;
  as?: "div" | "span";
}

const DIRECTION_CLASS: Record<string, string> = {
  up: "nps-animate-fade-in-up",
  down: "nps-animate-slide-down",
  none: "nps-animate-fade-in",
};

export function FadeIn({
  children,
  delay = 0,
  direction = "up",
  className = "",
  as: Tag = "div",
}: FadeInProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <Tag className={className}>{children}</Tag>;
  }

  const animClass = DIRECTION_CLASS[direction] ?? "nps-animate-fade-in";

  return (
    <Tag
      className={`nps-animate-initial ${animClass} ${className}`}
      style={delay > 0 ? { animationDelay: `${delay}ms` } : undefined}
    >
      {children}
    </Tag>
  );
}
