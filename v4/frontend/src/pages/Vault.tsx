export function Vault() {
  // TODO: Findings table with pagination and filtering
  // TODO: Summary stats
  // TODO: Search
  // TODO: Export controls (CSV/JSON)

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-text-bright">Vault</h2>

      {/* TODO: Vault summary stats */}
      {/* TODO: Findings data table */}
      {/* TODO: Search bar */}
      {/* TODO: Export buttons */}

      <div className="bg-nps-bg-card border border-nps-border rounded-lg p-4">
        <p className="text-nps-text-dim text-sm">
          Vault findings will be loaded from PostgreSQL via the API.
        </p>
      </div>
    </div>
  );
}
