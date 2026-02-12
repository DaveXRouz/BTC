interface PatternBadgeProps {
  pattern: string;
  priority: "high" | "medium" | "low";
  description?: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-nps-error/20 text-nps-error border-nps-error/30",
  medium: "bg-nps-warning/20 text-nps-warning border-nps-warning/30",
  low: "bg-nps-success/20 text-nps-success border-nps-success/30",
};

export function PatternBadge({
  pattern,
  priority,
  description,
}: PatternBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs rounded border ${PRIORITY_COLORS[priority]}`}
      title={description}
    >
      {pattern}
    </span>
  );
}
