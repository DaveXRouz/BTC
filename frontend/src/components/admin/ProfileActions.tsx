import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { AdminOracleProfile } from "@/types";

interface ProfileActionsProps {
  profile: AdminOracleProfile;
  onDelete: (id: number) => void;
}

export function ProfileActions({ profile, onDelete }: ProfileActionsProps) {
  const { t } = useTranslation();
  const [showConfirm, setShowConfirm] = useState(false);

  if (profile.deleted_at !== null) {
    return (
      <span className="text-xs text-[var(--nps-text-dim)]">
        {t("admin.status_deleted")}
      </span>
    );
  }

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        className="px-2 py-1 text-xs border border-red-500/50 text-red-400 rounded hover:bg-red-500/10"
      >
        {t("admin.action_delete")}
      </button>

      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6 max-w-sm w-full mx-4">
            <p className="text-[var(--nps-text)] mb-4">
              {t("admin.confirm_delete_profile", { name: profile.name })}
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm border border-[var(--nps-border)] rounded hover:bg-[var(--nps-bg-hover)]"
              >
                {t("common.cancel")}
              </button>
              <button
                onClick={() => {
                  onDelete(profile.id);
                  setShowConfirm(false);
                }}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                {t("common.delete")}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
