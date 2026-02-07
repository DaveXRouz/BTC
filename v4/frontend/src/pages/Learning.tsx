export function Learning() {
  // TODO: XP bar and level display
  // TODO: Capabilities list
  // TODO: AI insights feed
  // TODO: Recommendations
  // TODO: Pattern analysis visualization
  // TODO: Scoring weights display

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-ai-accent">AI Learning</h2>

      {/* TODO: Level / XP progress bar */}
      <div className="bg-nps-ai-bg border border-nps-ai-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-ai-text mb-2">
          Level 1 — Novice
        </h3>
        <div className="h-2 bg-nps-bg rounded-full overflow-hidden">
          <div
            className="h-full bg-nps-ai-accent rounded-full"
            style={{ width: "0%" }}
          />
        </div>
        <p className="text-xs text-nps-ai-text mt-1">0 / 100 XP</p>
      </div>

      {/* TODO: Insights list */}
      {/* TODO: Recommendations */}
      {/* TODO: Pattern analysis */}
    </div>
  );
}
