import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { SystemUser } from "@/types";

interface UserActionsProps {
  user: SystemUser;
  currentUserId: string;
  onRoleChange: (id: string, role: string) => void;
  onResetPassword: (id: string) => void;
  onStatusChange: (id: string, isActive: boolean) => void;
  tempPassword: string | null;
}

const ROLES = ["admin", "user", "readonly"] as const;

export function UserActions({
  user,
  currentUserId,
  onRoleChange,
  onResetPassword,
  onStatusChange,
  tempPassword,
}: UserActionsProps) {
  const { t } = useTranslation();
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [confirmAction, setConfirmAction] = useState<string | null>(null);
  const isSelf = user.id === currentUserId;

  const handleConfirm = () => {
    if (confirmAction === "reset") {
      onResetPassword(user.id);
    } else if (confirmAction === "deactivate") {
      onStatusChange(user.id, false);
    } else if (confirmAction === "activate") {
      onStatusChange(user.id, true);
    }
    setConfirmAction(null);
  };

  return (
    <div className="flex items-center gap-1 relative">
      {/* Role dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowRoleMenu(!showRoleMenu)}
          disabled={isSelf}
          title={
            isSelf ? t("admin.cannot_modify_self") : t("admin.action_edit_role")
          }
          className="px-2 py-1 text-xs border border-[var(--nps-border)] rounded hover:bg-[var(--nps-bg-hover)] disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {t("admin.action_edit_role")}
        </button>
        {showRoleMenu && !isSelf && (
          <div className="absolute top-full start-0 mt-1 bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded shadow-lg z-10 min-w-[120px]">
            {ROLES.filter((r) => r !== user.role).map((role) => (
              <button
                key={role}
                onClick={() => {
                  onRoleChange(user.id, role);
                  setShowRoleMenu(false);
                }}
                className="block w-full text-start px-3 py-2 text-xs hover:bg-[var(--nps-bg-hover)] text-[var(--nps-text)]"
              >
                {t(`admin.role_${role}`)}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Reset password */}
      <button
        onClick={() => setConfirmAction("reset")}
        className="px-2 py-1 text-xs border border-[var(--nps-border)] rounded hover:bg-[var(--nps-bg-hover)]"
      >
        {t("admin.action_reset_password")}
      </button>

      {/* Activate/Deactivate */}
      <button
        onClick={() =>
          setConfirmAction(user.is_active ? "deactivate" : "activate")
        }
        disabled={isSelf && user.is_active}
        title={isSelf ? t("admin.cannot_modify_self") : undefined}
        className={`px-2 py-1 text-xs border rounded hover:bg-[var(--nps-bg-hover)] disabled:opacity-30 disabled:cursor-not-allowed ${
          user.is_active
            ? "border-red-500/50 text-red-400"
            : "border-green-500/50 text-green-400"
        }`}
      >
        {user.is_active
          ? t("admin.action_deactivate")
          : t("admin.action_activate")}
      </button>

      {/* Confirmation modal */}
      {confirmAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6 max-w-sm w-full mx-4">
            <p className="text-[var(--nps-text)] mb-4">
              {confirmAction === "reset" &&
                t("admin.confirm_password_reset", {
                  username: user.username,
                })}
              {confirmAction === "deactivate" &&
                t("admin.confirm_deactivate", { username: user.username })}
              {confirmAction === "activate" &&
                t("admin.confirm_activate", { username: user.username })}
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setConfirmAction(null)}
                className="px-4 py-2 text-sm border border-[var(--nps-border)] rounded hover:bg-[var(--nps-bg-hover)]"
              >
                {t("common.cancel")}
              </button>
              <button
                onClick={handleConfirm}
                className="px-4 py-2 text-sm bg-[var(--nps-accent)] text-white rounded hover:opacity-90"
              >
                {t("common.confirm")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Show temp password */}
      {tempPassword && confirmAction === null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6 max-w-sm w-full mx-4">
            <p className="text-[var(--nps-text)] mb-2">
              {t("admin.password_reset_success", { password: tempPassword })}
            </p>
            <code className="block p-2 bg-[var(--nps-bg)] rounded text-sm font-mono text-[var(--nps-text-bright)] mb-4 select-all">
              {tempPassword}
            </code>
            <button
              onClick={() => onResetPassword("")}
              className="w-full px-4 py-2 text-sm bg-[var(--nps-accent)] text-white rounded hover:opacity-90"
            >
              {t("common.close")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
