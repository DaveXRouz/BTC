export function Oracle() {
  // TODO: Oracle reading display (FC60 + numerology + zodiac + Chinese)
  // TODO: Question mode input
  // TODO: Name cipher input
  // TODO: Daily insight display
  // TODO: Timing advisor visualization

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-oracle-accent">Oracle</h2>

      {/* TODO: Current reading panel */}
      <div className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-4">
          Current Reading
        </h3>
        <p className="text-nps-text-dim text-sm">
          Oracle readings from fc60, numerology, and timing engines.
        </p>
      </div>

      {/* TODO: Question form */}
      {/* TODO: Name cipher form */}
      {/* TODO: Daily insight */}
    </div>
  );
}
