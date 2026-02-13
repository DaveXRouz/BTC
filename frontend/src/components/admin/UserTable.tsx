import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import type { SystemUser, UserSortField, SortOrder } from "@/types";
import { UserActions } from "./UserActions";

interface UserTableProps {
  users: SystemUser[];
  total: number;
  loading: boolean;
  sortBy: UserSortField;
  sortOrder: SortOrder;
  onSort: (field: UserSortField) => void;
  onSearch: (query: string) => void;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  currentUserId: string;
  onRoleChange: (id: string, role: string) => void;
  onResetPassword: (id: string) => void;
  onStatusChange: (id: string, isActive: boolean) => void;
  tempPassword: string | null;
}

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-purple-500/20 text-purple-400",
  user: "bg-blue-500/20 text-blue-400",
  readonly: "bg-gray-500/20 text-gray-400",
};

function SortArrow({
  field,
  sortBy,
  sortOrder,
}: {
  field: UserSortField;
  sortBy: UserSortField;
  sortOrder: SortOrder;
}) {
  if (field !== sortBy) return <span className="opacity-30 ms-1">&#8597;</span>;
  return (
    <span className="ms-1">{sortOrder === "asc" ? "\u2191" : "\u2193"}</span>
  );
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return d.toLocaleDateString();
}

function formatRelative(dateStr: string | null, neverText: string): string {
  if (!dateStr) return neverText;
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString();
}

export function UserTable({
  users,
  total,
  loading,
  sortBy,
  sortOrder,
  onSort,
  onSearch,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  currentUserId,
  onRoleChange,
  onResetPassword,
  onStatusChange,
  tempPassword,
}: UserTableProps) {
  const { t } = useTranslation();
  const [searchInput, setSearchInput] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => onSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput, onSearch]);

  const from = page * pageSize + 1;
  const to = Math.min((page + 1) * pageSize, total);
  const totalPages = Math.ceil(total / pageSize);

  const columns: { key: UserSortField; label: string }[] = [
    { key: "username", label: t("admin.col_username") },
    { key: "role", label: t("admin.col_role") },
    { key: "created_at", label: t("admin.col_created") },
    { key: "last_login", label: t("admin.col_last_login") },
    { key: "is_active", label: t("admin.col_status") },
  ];

  return (
    <div className="space-y-4">
      {/* Search */}
      <input
        type="text"
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        placeholder={t("admin.search_users")}
        className="w-full max-w-sm px-3 py-2 bg-[var(--nps-bg)] border border-[var(--nps-border)] rounded text-sm text-[var(--nps-text)] placeholder:text-[var(--nps-text-dim)]"
      />

      {/* Table */}
      <div className="overflow-x-auto border border-[var(--nps-border)] rounded-lg">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--nps-border)] bg-[var(--nps-bg-card)]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => onSort(col.key)}
                  className="px-4 py-3 text-start font-medium text-[var(--nps-text-dim)] cursor-pointer hover:text-[var(--nps-text)] select-none"
                >
                  {col.label}
                  <SortArrow
                    field={col.key}
                    sortBy={sortBy}
                    sortOrder={sortOrder}
                  />
                </th>
              ))}
              <th className="px-4 py-3 text-start font-medium text-[var(--nps-text-dim)]">
                {t("admin.col_readings")}
              </th>
              <th className="px-4 py-3 text-start font-medium text-[var(--nps-text-dim)]">
                {t("admin.col_actions")}
              </th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr
                  key={`skeleton-${i}`}
                  className="border-b border-[var(--nps-border)]"
                >
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-[var(--nps-bg-hover)] rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))}
            {!loading && users.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-[var(--nps-text-dim)]"
                >
                  {t("admin.no_users")}
                </td>
              </tr>
            )}
            {!loading &&
              users.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-[var(--nps-border)] hover:bg-[var(--nps-bg-hover)]"
                >
                  <td className="px-4 py-3 font-mono text-[var(--nps-text)]">
                    {user.username}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${ROLE_COLORS[user.role] || ROLE_COLORS.readonly}`}
                    >
                      {t(`admin.role_${user.role}`)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                    {formatRelative(user.last_login, t("admin.never"))}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        user.is_active
                          ? "bg-green-500/20 text-green-400"
                          : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {user.is_active
                        ? t("admin.status_active")
                        : t("admin.status_inactive")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                    {user.reading_count}
                  </td>
                  <td className="px-4 py-3">
                    <UserActions
                      user={user}
                      currentUserId={currentUserId}
                      onRoleChange={onRoleChange}
                      onResetPassword={onResetPassword}
                      onStatusChange={onStatusChange}
                      tempPassword={tempPassword}
                    />
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-[var(--nps-text-dim)]">
          <span>{t("admin.page_info", { from, to, total })}</span>
          <div className="flex items-center gap-2">
            <span>{t("admin.page_size")}:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="bg-[var(--nps-bg)] border border-[var(--nps-border)] rounded px-2 py-1 text-[var(--nps-text)]"
            >
              {[10, 20, 50].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 0}
              className="px-3 py-1 border border-[var(--nps-border)] rounded disabled:opacity-30 hover:bg-[var(--nps-bg-hover)]"
            >
              {t("admin.page_prev")}
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 border border-[var(--nps-border)] rounded disabled:opacity-30 hover:bg-[var(--nps-bg-hover)]"
            >
              {t("admin.page_next")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
