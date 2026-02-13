import { useState } from "react";
import { useTranslation } from "react-i18next";
import { HealthDashboard } from "@/components/admin/HealthDashboard";
import { LogViewer } from "@/components/admin/LogViewer";
import { AnalyticsCharts } from "@/components/admin/AnalyticsCharts";

type MonitoringTab = "health" | "logs" | "analytics";

const TAB_IDS: MonitoringTab[] = ["health", "logs", "analytics"];
const TAB_KEYS: Record<MonitoringTab, string> = {
  health: "admin.monitoring_tab_health",
  logs: "admin.monitoring_tab_logs",
  analytics: "admin.monitoring_tab_analytics",
};

export function AdminMonitoring() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<MonitoringTab>("health");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[var(--nps-text-bright)]">
          {t("admin.monitoring_system_monitoring")}
        </h2>
      </div>

      {/* Tab navigation */}
      <div className="flex space-x-1 bg-[var(--nps-bg-card)] rounded-lg p-1 border border-[var(--nps-border)]">
        {TAB_IDS.map((id) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === id
                ? "bg-blue-600 text-white"
                : "text-[var(--nps-text-dim)] hover:text-[var(--nps-text-bright)] hover:bg-[var(--nps-bg-card)]/50"
            }`}
          >
            {t(TAB_KEYS[id])}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "health" && <HealthDashboard />}
      {activeTab === "logs" && <LogViewer />}
      {activeTab === "analytics" && <AnalyticsCharts />}
    </div>
  );
}

export default AdminMonitoring;
