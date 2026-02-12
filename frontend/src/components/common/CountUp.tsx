import { useState, useEffect, useRef, useCallback } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface CountUpProps {
  value: number;
  duration?: number;
  delay?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}

function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3;
}

export function CountUp({
  value,
  duration = 800,
  delay = 0,
  decimals = 0,
  prefix = "",
  suffix = "",
  className = "",
}: CountUpProps) {
  const reduced = useReducedMotion();
  const [display, setDisplay] = useState(reduced ? value : 0);
  const rafRef = useRef(0);
  const startRef = useRef<number | null>(null);
  const fromRef = useRef(0);

  const format = useCallback(
    (n: number) => {
      if (!isFinite(n)) return "\u2014";
      return `${prefix}${n.toFixed(decimals)}${suffix}`;
    },
    [decimals, prefix, suffix],
  );

  useEffect(() => {
    if (reduced) {
      setDisplay(value);
      return;
    }

    if (!isFinite(value)) {
      setDisplay(value);
      return;
    }

    const from = fromRef.current;
    const diff = value - from;

    if (diff === 0) return;

    let delayTimer: ReturnType<typeof setTimeout> | undefined;

    function animate(timestamp: number) {
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutCubic(progress);
      const current = from + diff * easedProgress;

      setDisplay(current);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        setDisplay(value);
        fromRef.current = value;
      }
    }

    function start() {
      startRef.current = null;
      rafRef.current = requestAnimationFrame(animate);
    }

    if (delay > 0) {
      delayTimer = setTimeout(start, delay);
    } else {
      start();
    }

    return () => {
      cancelAnimationFrame(rafRef.current);
      if (delayTimer !== undefined) clearTimeout(delayTimer);
      fromRef.current = value;
    };
  }, [value, duration, delay, reduced]);

  return <span className={className}>{format(display)}</span>;
}
