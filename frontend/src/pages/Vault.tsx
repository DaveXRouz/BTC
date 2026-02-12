import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/common/EmptyState";

export default function Vault() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-text-bright">
        {t("vault.title")}
      </h2>

      <div className="bg-nps-bg-card border border-nps-border rounded-lg p-4">
        <EmptyState icon="vault" title={t("vault.empty")} />
      </div>
    </div>
  );
}
