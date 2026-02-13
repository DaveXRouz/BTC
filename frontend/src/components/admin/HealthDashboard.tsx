import { useState, useEffect, useCallback } from "react";
import { adminHealth } from "@/services/api";
import type { DetailedHealth, ServiceStatus } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  healthy: "bg-green-500",
  unhealthy: "bg-red-500",
  degraded: "bg-yellow-500",
  not_connected: "bg-gray-400",
  not_deployed: "bg-gray-400",
  not_configured: "bg-gray-400",
  direct_mode: "bg-blue-400",
  configured: "bg-blue-400",
  external: "bg-blue-400",
};

function StatusIndicator({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "bg-gray-400";
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`} />;
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(" ");
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null) return "N/A";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

const SERVICE_LABELS: Record<string, string> = {
  api: "API",
  database: "Database",
  redis: "Redis",
  oracle_service: "Oracle",
  scanner_service: "Scanner",
  telegram: "Telegram",
  nginx: "Nginx",
};

function ServiceCard({
  name,
  service,
}: {
  name: string;
  service: ServiceStatus;
}) {
  const label = SERVICE_LABELS[name] || name;
  const detail =
    service.mode ||
    (service.used_memory_human ? `Mem: ${service.used_memory_human}` : null) ||
    (service.size_bytes != null
      ? `DB: ${formatBytes(service.size_bytes)}`
      : null) ||
    service.version ||
    service.note ||
    "";

  return (
    <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <StatusIndicator status={service.status} />
        <span className="text-sm font-medium text-[var(--nps-text-bright)]">
          {label}
        </span>
      </div>
      <p className="text-xs text-[var(--nps-text-dim)] capitalize">
        {service.status.replace(/_/g, " ")}
      </p>
      {detail && (
        <p className="text-xs text-[var(--nps-text-dim)] mt-1">{detail}</p>
      )}
      {service.error && (
        <p className="text-xs text-red-400 mt-1 truncate" title={service.error}>
          {service.error}
        </p>
      )}
    </div>
  );
}

export function HealthDashboard() {
  const [health, setHealth] = useState<DetailedHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await adminHealth.detailed();
      setHealth(data);
      setError(null);
      setLastRefresh(new Date());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch health data",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10_000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  if (loading && !health) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <div
              key={i}
              className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4 animate-pulse"
            >
              <div className="h-4 bg-gray-700 rounded w-2/3 mb-2" />
              <div className="h-3 bg-gray-700 rounded w-1/2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
        <p className="text-red-400 text-sm">{error}</p>
        <button
          onClick={fetchHealth}
          className="mt-2 text-sm text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!health) return null;

  return (
    <div className="space-y-4">
      {/* System info bar */}
      <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <StatusIndicator status={health.status} />
            <span className="font-medium text-[var(--nps-text-bright)] capitalize">
              {health.status}
            </span>
          </div>
          <span className="text-[var(--nps-text-dim)]">
            Uptime: {formatUptime(health.uptime_seconds)}
          </span>
          <span className="text-[var(--nps-text-dim)]">
            Memory: {health.system.process_memory_mb} MB
          </span>
          <span className="text-[var(--nps-text-dim)]">
            CPUs: {health.system.cpu_count}
          </span>
          <span className="text-[var(--nps-text-dim)]">
            Python {health.system.python_version}
          </span>
        </div>
      </div>

      {/* Service cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(health.services).map(([name, service]) => (
          <ServiceCard key={name} name={name} service={service} />
        ))}
      </div>

      {/* Footer with last refresh + refresh button */}
      <div className="flex items-center justify-between text-xs text-[var(--nps-text-dim)]">
        <span>
          Last refresh: {lastRefresh ? lastRefresh.toLocaleTimeString() : "—"}
        </span>
        <button
          onClick={fetchHealth}
          className="px-3 py-1 bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded text-[var(--nps-text-dim)] hover:text-[var(--nps-text-bright)] transition-colors"
        >
          Refresh Now
        </button>
      </div>
    </div>
  );
}
