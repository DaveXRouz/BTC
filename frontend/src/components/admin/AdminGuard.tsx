import { Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function AdminGuard() {
  const { t } = useTranslation();
  const role = localStorage.getItem("nps_user_role");

  if (role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-8 max-w-md w-full">
          <div className="text-4xl mb-4">403</div>
          <h2 className="text-xl font-bold text-[var(--nps-text-bright)] mb-2">
            {t("admin.forbidden_title")}
          </h2>
          <p className="text-[var(--nps-text-dim)]">
            {t("admin.forbidden_message")}
          </p>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
