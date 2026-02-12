import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

const ACTIONS = [
  {
    key: "time",
    icon: "🕐",
    colorClass: "border-nps-oracle-accent/50 hover:border-nps-oracle-accent",
  },
  {
    key: "question",
    icon: "❓",
    colorClass: "border-nps-gold/50 hover:border-nps-gold",
  },
  {
    key: "name",
    icon: "✍️",
    colorClass: "border-purple-500/50 hover:border-purple-500",
  },
] as const;

export function QuickActions() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div data-testid="quick-actions">
      <h2 className="text-lg font-semibold text-nps-text-bright mb-4">
        {t("dashboard.quick_actions")}
      </h2>
      <div className="grid grid-cols-3 gap-4">
        {ACTIONS.map(({ key, icon, colorClass }) => (
          <button
            key={key}
            onClick={() => navigate(`/oracle?type=${key}`)}
            className={`bg-nps-bg-card border rounded-xl p-4 flex flex-col items-center gap-2 transition-colors ${colorClass}`}
            data-testid={`quick-${key}`}
          >
            <span className="text-2xl">{icon}</span>
            <span className="text-sm text-nps-text-bright">
              {t(`dashboard.quick_${key}`)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
