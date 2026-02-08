import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { UserSelector } from "@/components/oracle/UserSelector";
import { UserForm } from "@/components/oracle/UserForm";
import {
  useOracleUsers,
  useCreateOracleUser,
  useUpdateOracleUser,
  useDeleteOracleUser,
} from "@/hooks/useOracleUsers";
import type { OracleUserCreate } from "@/types";

const SELECTED_USER_KEY = "nps_selected_oracle_user";

export function Oracle() {
  const { t } = useTranslation();
  const { data: users = [], isLoading } = useOracleUsers();
  const createUser = useCreateOracleUser();
  const updateUser = useUpdateOracleUser();
  const deleteUser = useDeleteOracleUser();

  const [selectedUserId, setSelectedUserId] = useState<number | null>(() => {
    const stored = localStorage.getItem(SELECTED_USER_KEY);
    return stored ? Number(stored) : null;
  });
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);

  // Persist selected user
  useEffect(() => {
    if (selectedUserId !== null) {
      localStorage.setItem(SELECTED_USER_KEY, String(selectedUserId));
    } else {
      localStorage.removeItem(SELECTED_USER_KEY);
    }
  }, [selectedUserId]);

  // Clear selection if user no longer exists
  useEffect(() => {
    if (
      selectedUserId !== null &&
      users.length > 0 &&
      !users.find((u) => u.id === selectedUserId)
    ) {
      setSelectedUserId(null);
    }
  }, [users, selectedUserId]);

  const selectedUser = users.find((u) => u.id === selectedUserId) ?? null;

  function handleCreate(data: OracleUserCreate) {
    createUser.mutate(data, {
      onSuccess: (newUser) => {
        setSelectedUserId(newUser.id);
        setFormMode(null);
      },
    });
  }

  function handleUpdate(data: OracleUserCreate) {
    if (selectedUserId === null) return;
    updateUser.mutate(
      { id: selectedUserId, data },
      { onSuccess: () => setFormMode(null) },
    );
  }

  function handleDelete() {
    if (selectedUserId === null) return;
    deleteUser.mutate(selectedUserId, {
      onSuccess: () => {
        setSelectedUserId(null);
        setFormMode(null);
      },
    });
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-nps-oracle-accent">
        {t("oracle.title")} — {t("oracle.subtitle")}
      </h2>

      {/* User Profile Section */}
      <section className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-3">
          {t("oracle.user_profile")}
        </h3>
        <UserSelector
          users={users}
          selectedId={selectedUserId}
          onSelect={setSelectedUserId}
          onAddNew={() => setFormMode("create")}
          onEdit={() => setFormMode("edit")}
          isLoading={isLoading}
        />
        {selectedUser && (
          <div className="mt-3 text-sm text-nps-text-dim">
            {t("oracle.field_birthday")}: {selectedUser.birthday}
            {selectedUser.country && ` · ${selectedUser.country}`}
            {selectedUser.city && `, ${selectedUser.city}`}
          </div>
        )}
      </section>

      {/* Oracle Reading Placeholder */}
      <section className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-3">
          {t("oracle.current_reading")}
        </h3>
        <p className="text-nps-text-dim text-sm">
          {selectedUser
            ? t("oracle.reading_ready")
            : t("oracle.select_to_begin")}
        </p>
      </section>

      {/* Reading Results Placeholder */}
      <section className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-3">
          {t("oracle.reading_results")}
        </h3>
        <p className="text-nps-text-dim text-sm">
          {t("oracle.results_placeholder")}
        </p>
      </section>

      {/* Reading History Placeholder */}
      <section className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-3">
          {t("oracle.reading_history")}
        </h3>
        <p className="text-nps-text-dim text-sm">
          {t("oracle.history_placeholder")}
        </p>
      </section>

      {/* User Form Modal */}
      {formMode === "create" && (
        <UserForm
          onSubmit={handleCreate}
          onCancel={() => setFormMode(null)}
          isSubmitting={createUser.isPending}
        />
      )}
      {formMode === "edit" && selectedUser && (
        <UserForm
          user={selectedUser}
          onSubmit={handleUpdate}
          onCancel={() => setFormMode(null)}
          onDelete={handleDelete}
          isSubmitting={updateUser.isPending}
        />
      )}
    </div>
  );
}
