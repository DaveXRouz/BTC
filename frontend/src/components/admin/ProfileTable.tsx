import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import type { AdminOracleProfile, ProfileSortField, SortOrder } from "@/types";
import { ProfileActions } from "./ProfileActions";

interface ProfileTableProps {
  profiles: AdminOracleProfile[];
  total: number;
  loading: boolean;
  sortBy: ProfileSortField;
  sortOrder: SortOrder;
  onSort: (field: ProfileSortField) => void;
  onSearch: (query: string) => void;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onDelete: (id: number) => void;
}

function SortArrow({
  field,
  sortBy,
  sortOrder,
}: {
  field: ProfileSortField;
  sortBy: ProfileSortField;
  sortOrder: SortOrder;
}) {
  if (field !== sortBy) return <span className="opacity-30 ms-1">&#8597;</span>;
  return (
    <span className="ms-1">{sortOrder === "asc" ? "\u2191" : "\u2193"}</span>
  );
}

export function ProfileTable({
  profiles,
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
  onDelete,
}: ProfileTableProps) {
  const { t } = useTranslation();
  const [searchInput, setSearchInput] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => onSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput, onSearch]);

  const from = page * pageSize + 1;
  const to = Math.min((page + 1) * pageSize, total);
  const totalPages = Math.ceil(total / pageSize);

  const columns: { key: ProfileSortField; label: string }[] = [
    { key: "name", label: t("admin.col_name") },
    { key: "birthday", label: t("admin.col_birthday") },
    { key: "created_at", label: t("admin.col_created") },
  ];

  return (
    <div className="space-y-4">
      {/* Search */}
      <input
        type="text"
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        placeholder={t("admin.search_profiles")}
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
                {t("admin.col_name_persian")}
              </th>
              <th className="px-4 py-3 text-start font-medium text-[var(--nps-text-dim)]">
                {t("admin.col_location")}
              </th>
              <th className="px-4 py-3 text-start font-medium text-[var(--nps-text-dim)]">
                {t("admin.col_readings")}
              </th>
              <th className="px-4 py-3 text-start font-medium text-[var(--nps-text-dim)]">
                {t("admin.col_status")}
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
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-[var(--nps-bg-hover)] rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))}
            {!loading && profiles.length === 0 && (
              <tr>
                <td
                  colSpan={8}
                  className="px-4 py-8 text-center text-[var(--nps-text-dim)]"
                >
                  {t("admin.no_profiles")}
                </td>
              </tr>
            )}
            {!loading &&
              profiles.map((profile) => {
                const isDeleted = profile.deleted_at !== null;
                return (
                  <tr
                    key={profile.id}
                    className={`border-b border-[var(--nps-border)] ${
                      isDeleted
                        ? "opacity-50"
                        : "hover:bg-[var(--nps-bg-hover)]"
                    }`}
                  >
                    <td className="px-4 py-3 text-[var(--nps-text)]">
                      {profile.name}
                    </td>
                    <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                      {profile.birthday}
                    </td>
                    <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                      {new Date(profile.created_at).toLocaleDateString()}
                    </td>
                    <td
                      className="px-4 py-3 text-[var(--nps-text-dim)]"
                      dir="rtl"
                    >
                      {profile.name_persian || "-"}
                    </td>
                    <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                      {[profile.country, profile.city]
                        .filter(Boolean)
                        .join(", ") || "-"}
                    </td>
                    <td className="px-4 py-3 text-[var(--nps-text-dim)]">
                      {profile.reading_count}
                    </td>
                    <td className="px-4 py-3">
                      {isDeleted ? (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400">
                          {t("admin.status_deleted")}
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400">
                          {t("admin.status_active")}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <ProfileActions profile={profile} onDelete={onDelete} />
                    </td>
                  </tr>
                );
              })}
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
