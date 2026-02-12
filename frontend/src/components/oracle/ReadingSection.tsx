import { useState } from "react";

interface ReadingSectionProps {
  title: string;
  icon?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  priority?: "high" | "medium" | "low";
  className?: string;
}

const PRIORITY_BORDER: Record<string, string> = {
  high: "border-nps-error/50",
  medium: "border-nps-warning/50",
  low: "border-nps-success/50",
};

export function ReadingSection({
  title,
  icon,
  children,
  defaultOpen = true,
  priority,
  className = "",
}: ReadingSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  const borderClass = priority
    ? PRIORITY_BORDER[priority]
    : "border-nps-oracle-border";

  return (
    <div
      data-reading-section
      className={`border ${borderClass} rounded-lg bg-nps-bg-card overflow-hidden animate-fade-in-up ${className}`}
    >
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-nps-text-bright hover:bg-nps-bg-hover transition-colors"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          {icon && <span aria-hidden="true">{icon}</span>}
          {title}
        </span>
        <span className="text-nps-text-dim text-xs">
          {open ? "\u25B2" : "\u25BC"}
        </span>
      </button>
      {open && (
        <div className="px-4 pb-4 border-t border-nps-border/30">
          {children}
        </div>
      )}
    </div>
  );
}
