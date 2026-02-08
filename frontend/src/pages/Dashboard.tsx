import { StatsCard } from "@/components/StatsCard";

export function Dashboard() {
  // TODO: Fetch real data from API
  // TODO: Subscribe to WebSocket events for live updates

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-text-bright">Dashboard</h2>

      {/* Stats grid — mirrors V3 dashboard_tab.py moment panel */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatsCard label="Keys Tested" value="0" />
        <StatsCard label="Seeds Tested" value="0" />
        <StatsCard label="Hits" value="0" color="#3fb950" />
        <StatsCard label="Speed" value="0/s" />
      </div>

      {/* TODO: Scanner status panel */}
      {/* TODO: Terminal status grid */}
      {/* TODO: AI brain insights */}
      {/* TODO: Live feed table */}
      {/* TODO: High score alert panel */}
    </div>
  );
}
