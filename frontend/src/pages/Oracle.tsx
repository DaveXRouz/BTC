import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ReadingTypeSelector,
  type ReadingType,
} from "@/components/oracle/ReadingTypeSelector";
import { OracleConsultationForm } from "@/components/oracle/OracleConsultationForm";
import { LoadingAnimation } from "@/components/oracle/LoadingAnimation";
import { ReadingResults } from "@/components/oracle/ReadingResults";
import { MultiUserSelector } from "@/components/oracle/MultiUserSelector";
import { UserForm } from "@/components/oracle/UserForm";
import {
  useOracleUsers,
  useCreateOracleUser,
  useUpdateOracleUser,
  useDeleteOracleUser,
} from "@/hooks/useOracleUsers";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import type {
  OracleUserCreate,
  SelectedUsers,
  ConsultationResult,
} from "@/types";

const SELECTED_USER_KEY = "nps_selected_oracle_user";
const VALID_TYPES: ReadingType[] = [
  "time",
  "name",
  "question",
  "daily",
  "multi",
];

export default function Oracle() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const rawType = searchParams.get("type");
  const readingType: ReadingType = VALID_TYPES.includes(rawType as ReadingType)
    ? (rawType as ReadingType)
    : "time";

  // User data
  const { data: users = [], isLoading: usersLoading } = useOracleUsers();
  const createUser = useCreateOracleUser();
  const updateUser = useUpdateOracleUser();
  const deleteUser = useDeleteOracleUser();

  const [selectedUsers, setSelectedUsers] = useState<SelectedUsers | null>(
    null,
  );
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Reading state
  const [consultationResult, setConsultationResult] =
    useState<ConsultationResult | null>(null);
  const readingProgress = useReadingProgress();
  const [isLoading, setIsLoading] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

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

  const primaryUser = selectedUsers?.primary ?? null;

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

  function handleTypeChange(type: ReadingType) {
    setSearchParams({ type });
    setConsultationResult(null);
  }

  function handleResult(result: ConsultationResult) {
    setConsultationResult(result);
    setIsLoading(false);
    requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  function handleLoadingChange(loading: boolean) {
    setIsLoading(loading);
  }

  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
      {/* LEFT PANEL */}
      <aside className="w-full lg:w-80 lg:flex-shrink-0 lg:sticky lg:top-6 lg:self-start space-y-4">
        {/* User Profile Card */}
        <section className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-3">
            {t("oracle.user_profile")}
          </h3>
          {readingType === "multi" ? (
            <MultiUserSelector
              users={users}
              selectedUsers={selectedUsers}
              onChange={setSelectedUsers}
              onAddNew={() => setFormMode("create")}
              onEdit={() => setFormMode("edit")}
              isLoading={usersLoading}
            />
          ) : (
            <div className="space-y-2">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 flex-wrap">
                <select
                  value={primaryUser?.id ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (!val) {
                      setSelectedUsers(null);
                      return;
                    }
                    const user = users.find((u) => u.id === Number(val));
                    if (user)
                      setSelectedUsers({
                        primary: user,
                        secondary: [],
                      });
                  }}
                  className="bg-[var(--nps-bg-input)] border border-[var(--nps-border)] text-[var(--nps-text)] rounded px-3 py-2 text-sm w-full sm:w-auto sm:min-w-[160px] min-h-[44px] sm:min-h-0 focus:outline-none focus:border-[var(--nps-accent)]"
                  aria-label={t("oracle.select_profile")}
                >
                  <option value="">
                    {users.length === 0
                      ? t("oracle.no_profiles")
                      : t("oracle.select_profile")}
                  </option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => setFormMode("create")}
                  className="px-3 py-2 text-xs bg-[var(--nps-accent)]/20 text-[var(--nps-accent)] border border-[var(--nps-border)] rounded hover:bg-[var(--nps-accent)]/30 transition-colors min-h-[44px] sm:min-h-0 w-full sm:w-auto"
                >
                  + {t("oracle.add_new_profile")}
                </button>
                {primaryUser && (
                  <button
                    type="button"
                    onClick={() => setFormMode("edit")}
                    className="px-3 py-2 text-xs text-[var(--nps-text-dim)] border border-[var(--nps-border)] rounded hover:text-[var(--nps-text)] transition-colors min-h-[44px] sm:min-h-0 w-full sm:w-auto"
                  >
                    {t("oracle.edit_profile")}
                  </button>
                )}
              </div>
              {primaryUser && (
                <div className="text-xs text-[var(--nps-text-dim)]">
                  {t("oracle.field_birthday")}: {primaryUser.birthday}
                  {primaryUser.country && ` · ${primaryUser.country}`}
                  {primaryUser.city && `, ${primaryUser.city}`}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Reading Type Card */}
        <section className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-3">
            {t("oracle.reading_type")}
          </h3>
          <ReadingTypeSelector
            value={readingType}
            onChange={handleTypeChange}
            disabled={isLoading}
          />
        </section>
      </aside>

      {/* MAIN AREA */}
      <main className="flex-1 space-y-6">
        {/* Form / Loading Card */}
        <section
          id="oracle-form-panel"
          role="tabpanel"
          className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4 lg:p-6 min-h-[300px]"
        >
          <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-4">
            {t(`oracle.type_${readingType}_title`)}
          </h3>
          {isLoading ? (
            <LoadingAnimation
              step={readingProgress.progress}
              total={100}
              message={
                readingProgress.message || t("oracle.loading_generating")
              }
              onCancel={() => {
                setIsLoading(false);
              }}
            />
          ) : primaryUser || readingType === "daily" ? (
            <OracleConsultationForm
              readingType={readingType}
              userId={primaryUser?.id ?? 0}
              userName={primaryUser?.name ?? ""}
              selectedUsers={selectedUsers}
              onResult={handleResult}
              onLoadingChange={handleLoadingChange}
            />
          ) : (
            <p className="text-[var(--nps-text-dim)] text-sm">
              {t("oracle.select_to_begin")}
            </p>
          )}
        </section>

        {/* Results Card */}
        <section
          ref={resultsRef}
          className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4 lg:p-6"
        >
          <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-3">
            {t("oracle.reading_results")}
          </h3>
          <ReadingResults result={consultationResult} />
        </section>
      </main>

      {/* UserForm Modal */}
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
