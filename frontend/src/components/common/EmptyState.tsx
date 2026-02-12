type IconVariant =
  | "readings"
  | "profiles"
  | "vault"
  | "search"
  | "learning"
  | "generic";

interface EmptyStateProps {
  icon?: IconVariant;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const ICON_MAP: Record<IconVariant, string> = {
  readings: "\uD83D\uDD2E",
  profiles: "\uD83D\uDC64",
  vault: "\uD83D\uDD12",
  search: "\uD83D\uDD0D",
  learning: "\uD83E\uDDE0",
  generic: "\uD83D\uDCE6",
};

export function EmptyState({
  icon = "generic",
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-8 text-center"
      data-testid="empty-state"
    >
      <span
        className="text-5xl mb-3 text-nps-oracle-accent"
        role="img"
        aria-hidden="true"
      >
        {ICON_MAP[icon]}
      </span>
      <p className="text-sm font-medium text-nps-text mb-1">{title}</p>
      {description && (
        <p className="text-xs text-nps-text-dim max-w-xs">{description}</p>
      )}
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-3 px-4 py-2 text-sm bg-nps-bg-button text-white rounded hover:opacity-90 transition-opacity"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
