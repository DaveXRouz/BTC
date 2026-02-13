import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAdminStats } from "@/hooks/useAdmin";

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
      <p className="text-xs text-[var(--nps-text-dim)] mb-1">{label}</p>
      <p className="text-2xl font-bold text-[var(--nps-text-bright)]">
        {value}
      </p>
    </div>
  );
}

export default function Admin() {
  const { t } = useTranslation();
  const { data: stats } = useAdminStats();

  const tabClass = (isActive: boolean) =>
    `px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
      isActive
        ? "border-[var(--nps-accent)] text-[var(--nps-accent)]"
        : "border-transparent text-[var(--nps-text-dim)] hover:text-[var(--nps-text)]"
    }`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-[var(--nps-text-bright)]">
          {t("admin.title")}
        </h1>
        <p className="text-sm text-[var(--nps-text-dim)]">
          {t("admin.subtitle")}
        </p>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label={t("admin.total_users")} value={stats.total_users} />
          <StatCard
            label={t("admin.active_users")}
            value={stats.active_users}
          />
          <StatCard
            label={t("admin.total_profiles")}
            value={stats.total_oracle_profiles}
          />
          <StatCard
            label={t("admin.readings_today")}
            value={stats.readings_today}
          />
        </div>
      )}

      {/* Tab navigation */}
      <div className="flex border-b border-[var(--nps-border)]">
        <NavLink
          to="/admin/users"
          className={({ isActive }) => tabClass(isActive)}
        >
          {t("admin.tab_users")}
        </NavLink>
        <NavLink
          to="/admin/profiles"
          className={({ isActive }) => tabClass(isActive)}
        >
          {t("admin.tab_profiles")}
        </NavLink>
      </div>

      {/* Nested content */}
      <Outlet />
    </div>
  );
}
