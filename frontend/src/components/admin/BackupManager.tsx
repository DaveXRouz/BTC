import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { admin as adminApi } from "@/services/api";
import type {
  BackupInfo,
  BackupListResponse,
  BackupTriggerResponse,
  RestoreResponse,
  BackupDeleteResponse,
} from "@/types";

const TYPE_BADGES: Record<string, { bg: string; text: string; label: string }> =
  {
    oracle_full: {
      bg: "bg-blue-500/20",
      text: "text-blue-400",
      label: "Oracle Full",
    },
    oracle_data: {
      bg: "bg-cyan-500/20",
      text: "text-cyan-400",
      label: "Oracle Data",
    },
    full_database: {
      bg: "bg-purple-500/20",
      text: "text-purple-400",
      label: "Full DB",
    },
  };

function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function BackupManager() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: backupList, isLoading } = useQuery<BackupListResponse>({
    queryKey: ["admin", "backups"],
    queryFn: () => adminApi.backups(),
    staleTime: 30_000,
  });

  const triggerBackup = useMutation<BackupTriggerResponse, Error, string>({
    mutationFn: (backupType: string) => adminApi.triggerBackup(backupType),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "backups"] }),
  });

  const restoreBackup = useMutation<RestoreResponse, Error, string>({
    mutationFn: (filename: string) => adminApi.restoreBackup(filename),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "backups"] }),
  });

  const deleteBackup = useMutation<BackupDeleteResponse, Error, string>({
    mutationFn: (filename: string) => adminApi.deleteBackup(filename),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "backups"] }),
  });

  const [showCreateMenu, setShowCreateMenu] = useState(false);
  const [restoreTarget, setRestoreTarget] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [restoreConfirmText, setRestoreConfirmText] = useState("");
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Auto-dismiss status after 5s
  useEffect(() => {
    if (statusMessage) {
      const timer = setTimeout(() => setStatusMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [statusMessage]);

  const handleTriggerBackup = async (backupType: string) => {
    setShowCreateMenu(false);
    try {
      const result = await triggerBackup.mutateAsync(backupType);
      if (result.status === "success") {
        setStatusMessage({ type: "success", text: t("admin.backup_success") });
      } else {
        setStatusMessage({
          type: "error",
          text: `${t("admin.backup_failed")}: ${result.message}`,
        });
      }
    } catch {
      setStatusMessage({ type: "error", text: t("admin.backup_failed") });
    }
  };

  const handleRestore = async () => {
    if (!restoreTarget) return;
    try {
      const result = await restoreBackup.mutateAsync(restoreTarget);
      setRestoreTarget(null);
      setRestoreConfirmText("");
      if (result.status === "success") {
        setStatusMessage({
          type: "success",
          text: t("admin.restore_success"),
        });
      } else {
        setStatusMessage({
          type: "error",
          text: `${t("admin.restore_failed")}: ${result.message}`,
        });
      }
    } catch {
      setRestoreTarget(null);
      setRestoreConfirmText("");
      setStatusMessage({ type: "error", text: t("admin.restore_failed") });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteBackup.mutateAsync(deleteTarget);
      setDeleteTarget(null);
      setStatusMessage({
        type: "success",
        text: t("admin.delete_backup") + " - OK",
      });
    } catch {
      setDeleteTarget(null);
      setStatusMessage({ type: "error", text: t("admin.backup_failed") });
    }
  };

  const backups = backupList?.backups ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--nps-text-bright)]">
          {t("admin.backup_manager")}
        </h2>
        <div className="relative">
          <button
            onClick={() => setShowCreateMenu(!showCreateMenu)}
            disabled={triggerBackup.isPending}
            className="px-4 py-2 bg-[var(--nps-accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {triggerBackup.isPending
              ? t("admin.backup_in_progress")
              : t("admin.trigger_backup")}
          </button>
          {showCreateMenu && (
            <div className="absolute end-0 mt-1 w-52 bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg shadow-lg z-10">
              {[
                {
                  type: "oracle_full",
                  label: t("admin.backup_type_oracle_full"),
                },
                {
                  type: "oracle_data",
                  label: t("admin.backup_type_oracle_data"),
                },
                {
                  type: "full_database",
                  label: t("admin.backup_type_full_database"),
                },
              ].map((opt) => (
                <button
                  key={opt.type}
                  onClick={() => handleTriggerBackup(opt.type)}
                  className="w-full text-start px-4 py-2 text-sm text-[var(--nps-text)] hover:bg-[var(--nps-bg-hover)] first:rounded-t-lg last:rounded-b-lg"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div
          role="alert"
          className={`px-4 py-3 rounded-lg text-sm font-medium ${
            statusMessage.type === "success"
              ? "bg-green-500/20 text-green-400 border border-green-500/30"
              : "bg-red-500/20 text-red-400 border border-red-500/30"
          }`}
        >
          {statusMessage.text}
        </div>
      )}

      {/* Schedule info */}
      <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
        <h3 className="text-sm font-medium text-[var(--nps-text-bright)] mb-2">
          {t("admin.backup_schedule")}
        </h3>
        <ul className="text-xs text-[var(--nps-text-dim)] space-y-1">
          <li>{t("admin.backup_schedule_daily")}</li>
          <li>{t("admin.backup_schedule_weekly")}</li>
        </ul>
        <p className="text-xs text-[var(--nps-text-dim)] mt-2">
          {t("admin.backup_retention")}:{" "}
          {backupList?.retention_policy ?? "Oracle: 30 days, Full: 60 days"}
        </p>
      </div>

      {/* Backup table */}
      {isLoading ? (
        <div className="text-center py-8 text-[var(--nps-text-dim)]">
          {t("common.loading")}
        </div>
      ) : backups.length === 0 ? (
        <div className="text-center py-8 text-[var(--nps-text-dim)]">
          {t("admin.no_backups")}
        </div>
      ) : (
        <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--nps-border)]">
                <th className="text-start px-4 py-3 text-xs text-[var(--nps-text-dim)] font-medium">
                  Filename
                </th>
                <th className="text-start px-4 py-3 text-xs text-[var(--nps-text-dim)] font-medium">
                  {t("admin.backup_type")}
                </th>
                <th className="text-start px-4 py-3 text-xs text-[var(--nps-text-dim)] font-medium">
                  {t("admin.backup_date")}
                </th>
                <th className="text-start px-4 py-3 text-xs text-[var(--nps-text-dim)] font-medium">
                  {t("admin.backup_size")}
                </th>
                <th className="text-end px-4 py-3 text-xs text-[var(--nps-text-dim)] font-medium">
                  {t("admin.col_actions")}
                </th>
              </tr>
            </thead>
            <tbody>
              {backups.map((backup: BackupInfo) => {
                const badge = TYPE_BADGES[backup.type] ?? {
                  bg: "bg-gray-500/20",
                  text: "text-gray-400",
                  label: backup.type,
                };
                return (
                  <tr
                    key={backup.filename}
                    className="border-b border-[var(--nps-border)] last:border-b-0"
                  >
                    <td
                      className="px-4 py-3 text-[var(--nps-text)] truncate max-w-[200px]"
                      title={backup.filename}
                    >
                      {backup.filename}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${badge.bg} ${badge.text}`}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td
                      className="px-4 py-3 text-[var(--nps-text-dim)]"
                      title={new Date(backup.timestamp).toLocaleString()}
                    >
                      {formatRelativeTime(backup.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                      {backup.size_human}
                    </td>
                    <td className="px-4 py-3 text-end space-x-2">
                      <button
                        onClick={() => setRestoreTarget(backup.filename)}
                        disabled={restoreBackup.isPending}
                        className="px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded hover:bg-amber-500/30 disabled:opacity-50"
                      >
                        {t("admin.restore_backup")}
                      </button>
                      <button
                        onClick={() => setDeleteTarget(backup.filename)}
                        disabled={deleteBackup.isPending}
                        className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 disabled:opacity-50"
                      >
                        {t("admin.delete_backup")}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Restore confirmation modal */}
      {restoreTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-[var(--nps-text-bright)] mb-2">
              {t("admin.backup_confirm_restore_title")}
            </h3>
            <p className="text-sm text-[var(--nps-text-dim)] mb-4">
              {t("admin.backup_confirm_restore")}
            </p>
            <p className="text-xs text-[var(--nps-text-dim)] mb-2">
              {t("admin.backup_confirm_restore_type")}
            </p>
            <input
              type="text"
              value={restoreConfirmText}
              onChange={(e) => setRestoreConfirmText(e.target.value)}
              placeholder="RESTORE"
              className="w-full px-3 py-2 bg-[var(--nps-bg)] border border-[var(--nps-border)] rounded text-sm text-[var(--nps-text)] mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setRestoreTarget(null);
                  setRestoreConfirmText("");
                }}
                className="px-4 py-2 text-sm text-[var(--nps-text-dim)] hover:text-[var(--nps-text)]"
              >
                {t("common.cancel")}
              </button>
              <button
                onClick={handleRestore}
                disabled={
                  restoreConfirmText !== "RESTORE" || restoreBackup.isPending
                }
                className="px-4 py-2 text-sm bg-amber-600 text-white rounded-lg disabled:opacity-50 hover:bg-amber-700"
              >
                {restoreBackup.isPending
                  ? t("admin.restore_in_progress")
                  : t("common.confirm")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-[var(--nps-text-bright)] mb-2">
              {t("admin.delete_backup")}
            </h3>
            <p className="text-sm text-[var(--nps-text-dim)] mb-4">
              {t("admin.backup_confirm_delete")}
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-sm text-[var(--nps-text-dim)] hover:text-[var(--nps-text)]"
              >
                {t("common.cancel")}
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteBackup.isPending}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg disabled:opacity-50 hover:bg-red-700"
              >
                {t("common.delete")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BackupManager;
