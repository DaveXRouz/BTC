import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { UserTable } from "@/components/admin/UserTable";
import {
  useAdminUsers,
  useUpdateRole,
  useResetPassword,
  useUpdateStatus,
} from "@/hooks/useAdmin";
import type { UserSortField, SortOrder } from "@/types";

export default function AdminUsers() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<UserSortField>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  const currentUserId = localStorage.getItem("nps_user_id") || "";

  const { data, isLoading, error } = useAdminUsers({
    limit: pageSize,
    offset: page * pageSize,
    search: search || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const roleMutation = useUpdateRole();
  const passwordMutation = useResetPassword();
  const statusMutation = useUpdateStatus();

  const handleSort = useCallback(
    (field: UserSortField) => {
      if (field === sortBy) {
        setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        setSortBy(field);
        setSortOrder("asc");
      }
      setPage(0);
    },
    [sortBy],
  );

  const handleSearch = useCallback((q: string) => {
    setSearch(q);
    setPage(0);
  }, []);

  const handleRoleChange = useCallback(
    (id: string, role: string) => {
      roleMutation.mutate({ id, role });
    },
    [roleMutation],
  );

  const handleResetPassword = useCallback(
    (id: string) => {
      if (id === "") {
        setTempPassword(null);
        return;
      }
      passwordMutation.mutate(id, {
        onSuccess: (data) => setTempPassword(data.temporary_password),
      });
    },
    [passwordMutation],
  );

  const handleStatusChange = useCallback(
    (id: string, isActive: boolean) => {
      statusMutation.mutate({ id, is_active: isActive });
    },
    [statusMutation],
  );

  if (error) {
    return (
      <div className="text-center py-8 text-red-400">
        {t("admin.error_load_users")}
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-[var(--nps-text-bright)] mb-4">
        {t("admin.users_title")}
      </h2>
      <UserTable
        users={data?.users || []}
        total={data?.total || 0}
        loading={isLoading}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
        onSearch={handleSearch}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(0);
        }}
        currentUserId={currentUserId}
        onRoleChange={handleRoleChange}
        onResetPassword={handleResetPassword}
        onStatusChange={handleStatusChange}
        tempPassword={tempPassword}
      />
    </div>
  );
}
