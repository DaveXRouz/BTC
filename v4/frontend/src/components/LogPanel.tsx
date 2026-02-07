interface LogEntry {
  timestamp: string;
  message: string;
  level?: "info" | "warning" | "error" | "success";
}

interface LogPanelProps {
  title: string;
  entries: LogEntry[];
  maxHeight?: string;
}

const levelColors = {
  info: "text-nps-text",
  warning: "text-nps-warning",
  error: "text-nps-error",
  success: "text-nps-success",
};

export function LogPanel({
  title,
  entries,
  maxHeight = "300px",
}: LogPanelProps) {
  return (
    <div className="bg-nps-bg-card border border-nps-border rounded-lg">
      <div className="px-4 py-2 border-b border-nps-border">
        <h3 className="text-sm font-semibold text-nps-text">{title}</h3>
      </div>
      <div
        className="overflow-auto font-mono text-xs p-2"
        style={{ maxHeight }}
      >
        {entries.length === 0 ? (
          <p className="text-nps-text-dim p-2">No entries yet</p>
        ) : (
          entries.map((entry, i) => (
            <div key={i} className="flex gap-2 py-0.5">
              <span className="text-nps-text-dim whitespace-nowrap">
                {entry.timestamp}
              </span>
              <span className={levelColors[entry.level || "info"]}>
                {entry.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
