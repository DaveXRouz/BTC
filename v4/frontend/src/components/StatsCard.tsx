interface StatsCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}

export function StatsCard({ label, value, subtitle, color }: StatsCardProps) {
  return (
    <div className="bg-nps-bg-card border border-nps-border rounded-lg p-4">
      <p className="text-xs text-nps-text-dim uppercase tracking-wide">
        {label}
      </p>
      <p
        className="text-2xl font-mono font-bold mt-1"
        style={color ? { color } : undefined}
      >
        {value}
      </p>
      {subtitle && <p className="text-xs text-nps-text-dim mt-1">{subtitle}</p>}
    </div>
  );
}
