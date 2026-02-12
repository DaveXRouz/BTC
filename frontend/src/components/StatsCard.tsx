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

export function StatsCard({
  label,
  value,
  subtitle,
  color,
  icon,
  trend,
}: StatsCardProps) {
  return (
    <div className="bg-nps-bg-card border border-nps-border rounded-lg p-4">
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-sm">{icon}</span>}
        <p className="text-xs text-nps-text-dim uppercase tracking-wide">
          {label}
        </p>
      </div>
      <p
        className="text-2xl font-mono font-bold mt-1"
        style={color ? { color } : undefined}
      >
        {value}
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
