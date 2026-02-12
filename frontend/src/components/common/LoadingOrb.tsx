import { useReducedMotion } from "@/hooks/useReducedMotion";

interface LoadingOrbProps {
  label?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZE_CLASSES = {
  sm: { orb: "w-4 h-4", dot: "w-1.5 h-1.5", label: "text-xs" },
  md: { orb: "w-8 h-8", dot: "w-2.5 h-2.5", label: "text-sm" },
  lg: { orb: "w-12 h-12", dot: "w-3.5 h-3.5", label: "text-base" },
} as const;

export function LoadingOrb({
  label = "Loading...",
  size = "md",
  className = "",
}: LoadingOrbProps) {
  const reduced = useReducedMotion();
  const sizes = SIZE_CLASSES[size];

  return (
    <div
      className={`flex flex-col items-center gap-3 ${className}`}
      role="status"
      aria-label={label}
    >
      <div
        className={`${sizes.orb} rounded-full bg-nps-success/20 border border-nps-success/40 flex items-center justify-center ${reduced ? "" : "nps-animate-orb-pulse"}`}
        data-testid="loading-orb"
      >
        <div className={`${sizes.dot} rounded-full bg-nps-success`} />
      </div>
      <span className={`${sizes.label} text-nps-text-dim`}>{label}</span>
    </div>
  );
}
