import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/common/EmptyState";

export default function Learning() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-ai-accent">
        {t("learning.title")}
      </h2>

      <div className="bg-nps-ai-bg border border-nps-ai-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-ai-text mb-2">
          {t("learning.level_label", {
            level: 1,
            name: t("learning.level_novice"),
          })}
        </h3>
        <div className="h-2 bg-nps-bg rounded-full overflow-hidden">
          <div
            className="h-full bg-nps-ai-accent rounded-full"
            style={{ width: "0%" }}
          />
        </div>
        <p className="text-xs text-nps-ai-text mt-1">
          {t("learning.xp_progress", { current: 0, max: 100 })}
        </p>
      </div>

      <div className="bg-nps-ai-bg border border-nps-ai-border rounded-lg p-4">
        <EmptyState icon="learning" title={t("learning.empty")} />
      </div>
    </div>
  );
}
