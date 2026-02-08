import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { MultiUserSelector } from "@/components/oracle/MultiUserSelector";
import { UserForm } from "@/components/oracle/UserForm";
import {
  useOracleUsers,
  useCreateOracleUser,
  useUpdateOracleUser,
  useDeleteOracleUser,
} from "@/hooks/useOracleUsers";
import { OracleConsultationForm } from "@/components/oracle/OracleConsultationForm";
import { ReadingResults } from "@/components/oracle/ReadingResults";
import type {
  OracleUserCreate,
  SelectedUsers,
  ConsultationResult,
} from "@/types";

const SELECTED_USER_KEY = "nps_selected_oracle_user";

export function Oracle() {
  const { t } = useTranslation();
  const { data: users = [], isLoading } = useOracleUsers();
  const createUser = useCreateOracleUser();
  const updateUser = useUpdateOracleUser();
  const deleteUser = useDeleteOracleUser();

  const [selectedUsers, setSelectedUsers] = useState<SelectedUsers | null>(
    null,
  );
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [consultationResult, setConsultationResult] =
    useState<ConsultationResult | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Restore persisted primary user on load
  useEffect(() => {
    if (users.length === 0 || selectedUsers) return;
    const stored = localStorage.getItem(SELECTED_USER_KEY);
    if (stored) {
      const user = users.find((u) => u.id === Number(stored));
      if (user) {
        setSelectedUsers({ primary: user, secondary: [] });
      }
    }
  }, [users, selectedUsers]);

  // Persist selected primary user
  useEffect(() => {
    if (selectedUsers) {
      localStorage.setItem(SELECTED_USER_KEY, String(selectedUsers.primary.id));
    } else {
      localStorage.removeItem(SELECTED_USER_KEY);
    }
  }, [selectedUsers]);

  // Clear selection if primary user no longer exists
  useEffect(() => {
    if (
      selectedUsers &&
      users.length > 0 &&
      !users.find((u) => u.id === selectedUsers.primary.id)
    ) {
      setSelectedUsers(null);
    }
  }, [users, selectedUsers]);

  function handleCreate(data: OracleUserCreate) {
    setFormError(null);
    createUser.mutate(data, {
      onSuccess: (newUser) => {
        setSelectedUsers({ primary: newUser, secondary: [] });
        setFormMode(null);
        setFormError(null);
      },
      onError: (err) => setFormError(err.message),
    });
  }

  function handleUpdate(data: OracleUserCreate) {
    if (!selectedUsers) return;
    setFormError(null);
    updateUser.mutate(
      { id: selectedUsers.primary.id, data },
      {
        onSuccess: () => {
          setFormMode(null);
          setFormError(null);
        },
        onError: (err) => setFormError(err.message),
      },
    );
  }

  function handleDelete() {
    if (!selectedUsers) return;
    deleteUser.mutate(selectedUsers.primary.id, {
      onSuccess: () => {
        setSelectedUsers(null);
        setFormMode(null);
      },
    });
  }

  const primaryUser = selectedUsers?.primary ?? null;

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
        <MultiUserSelector
          users={users}
          selectedUsers={selectedUsers}
          onChange={setSelectedUsers}
          onAddNew={() => setFormMode("create")}
          onEdit={() => setFormMode("edit")}
          isLoading={isLoading}
        />
        {primaryUser && (
          <div className="mt-3 text-sm text-nps-text-dim">
            {t("oracle.field_birthday")}: {primaryUser.birthday}
            {primaryUser.country && ` · ${primaryUser.country}`}
            {primaryUser.city && `, ${primaryUser.city}`}
          </div>
        )}
      </section>

      {/* Oracle Consultation */}
      <section className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-3">
          {t("oracle.current_reading")}
        </h3>
        {primaryUser ? (
          <OracleConsultationForm
            userId={primaryUser.id}
            userName={primaryUser.name}
            onResult={setConsultationResult}
          />
        ) : (
          <p className="text-nps-text-dim text-sm">
            {t("oracle.select_to_begin")}
          </p>
        )}
      </section>

      {/* Reading Results + History (tabbed) */}
      <section className="bg-nps-oracle-bg border border-nps-oracle-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-nps-oracle-accent mb-3">
          {t("oracle.reading_results")}
        </h3>
        <ReadingResults result={consultationResult} />
      </section>

      {/* User Form Modal */}
      {formMode === "create" && (
        <UserForm
          onSubmit={handleCreate}
          onCancel={() => {
            setFormMode(null);
            setFormError(null);
          }}
          isSubmitting={createUser.isPending}
          serverError={formError}
        />
      )}
      {formMode === "edit" && primaryUser && (
        <UserForm
          user={primaryUser}
          onSubmit={handleUpdate}
          onCancel={() => {
            setFormMode(null);
            setFormError(null);
          }}
          onDelete={handleDelete}
          isSubmitting={updateUser.isPending}
          serverError={formError}
        />
      )}
    </div>
  );
}
