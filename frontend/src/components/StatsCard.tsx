import { CountUp } from "./common/CountUp";

interface StatsCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  color?: string;
  icon?: string;
  trend?: { direction: "up" | "down" | "flat"; value: string };
}

const TREND_STYLES = {
  up: "text-nps-success",
  down: "text-nps-error",
  flat: "text-nps-text-dim",
} as const;

const TREND_ARROWS = {
  up: "\u2191",
  down: "\u2193",
  flat: "\u2192",
} as const;

function parseNumericValue(value: string | number): {
  numeric: number | null;
  suffix: string;
  prefix: string;
} {
  if (typeof value === "number") {
    return { numeric: value, suffix: "", prefix: "" };
  }
  // Match patterns like "123", "0/s", "$100", "45%"
  const match = value.match(/^([^0-9]*?)(\d+(?:\.\d+)?)(.*)$/);
  if (match) {
    return {
      prefix: match[1],
      numeric: parseFloat(match[2]),
      suffix: match[3],
    };
  }
  return { numeric: null, suffix: "", prefix: "" };
}

export function StatsCard({
  label,
  value,
  subtitle,
  color,
  icon,
  trend,
}: StatsCardProps) {
  const parsed = parseNumericValue(value);

  return (
    <div
      role="group"
      aria-label={label}
      className="bg-nps-bg-card border border-nps-border rounded-lg p-4 min-h-[72px]"
    >
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-sm">{icon}</span>}
        <p className="text-xs text-nps-text-dim uppercase tracking-wide">
          {label}
        </p>
      </div>
      <p
        className="text-xl sm:text-2xl font-mono font-bold mt-1"
        style={color ? { color } : undefined}
      >
        {parsed.numeric !== null ? (
          <CountUp
            value={parsed.numeric}
            duration={800}
            prefix={parsed.prefix}
            suffix={parsed.suffix}
            decimals={String(value).includes(".") ? 1 : 0}
          />
        ) : (
          value
        )}
      </p>
      {trend && (
        <p className={`text-xs mt-1 ${TREND_STYLES[trend.direction]}`}>
          {TREND_ARROWS[trend.direction]} {trend.value}
        </p>
      )}
      {subtitle && <p className="text-xs text-nps-text-dim mt-1">{subtitle}</p>}
    </div>
  );
}
