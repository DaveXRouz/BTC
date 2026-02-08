export function Scanner() {
  // TODO: Scan config form (mode, chains, batch_size, threads, puzzle)
  // TODO: Terminal list with start/stop/pause controls
  // TODO: Live stats display
  // TODO: Live key feed (sampled from WebSocket stream)

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-text-bright">Scanner</h2>

      {/* TODO: Scan configuration form */}
      <div className="bg-nps-bg-card border border-nps-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-text mb-4">
          Scan Configuration
        </h3>
        <p className="text-nps-text-dim text-sm">
          Scanner controls will connect to the Rust scanner service via API.
        </p>
      </div>

      {/* TODO: Active terminals grid */}
      {/* TODO: Live feed table */}
      {/* TODO: Checkpoint management */}
    </div>
  );
}
