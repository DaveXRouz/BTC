import React from "react";
import type { ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { FadeIn } from "./FadeIn";

interface StaggerChildrenProps {
  children: ReactNode;
  staggerMs?: number;
  baseDelay?: number;
  animation?: "fade" | "slide" | "scale";
  className?: string;
}

const MAX_TOTAL_STAGGER = 800;

export function StaggerChildren({
  children,
  staggerMs = 50,
  baseDelay = 0,
  className = "",
}: StaggerChildrenProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <div className={className}>{children}</div>;
  }

  const childArray = React.Children.toArray(children);

  return (
    <div className={className}>
      {childArray.map((child, index) => {
        const delay = Math.min(
          baseDelay + staggerMs * index,
          baseDelay + MAX_TOTAL_STAGGER,
        );
        return (
          <FadeIn key={index} delay={delay} direction="up">
            {child}
          </FadeIn>
        );
      })}
    </div>
  );
}
