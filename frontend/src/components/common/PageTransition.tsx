import type { ReactNode } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface PageTransitionProps {
  children: ReactNode;
  locationKey: string;
}

export function PageTransition({ children, locationKey }: PageTransitionProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <>{children}</>;
  }

  return (
    <div key={locationKey} className="nps-animate-fade-in">
      {children}
    </div>
  );
}
