import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { OracleUser, SelectedUsers } from "@/types";
import { UserChip } from "./UserChip";

interface MultiUserSelectorProps {
  users: OracleUser[];
  selectedUsers: SelectedUsers | null;
  onChange: (selected: SelectedUsers | null) => void;
  onAddNew: () => void;
  onEdit: () => void;
  isLoading?: boolean;
}

const MAX_TOTAL_USERS = 5;

export function MultiUserSelector({
  users,
  selectedUsers,
  onChange,
  onAddNew,
  onEdit,
  isLoading,
}: MultiUserSelectorProps) {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const [showSecondaryDropdown, setShowSecondaryDropdown] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-nps-text-dim text-sm">
        <div className="h-4 w-4 border-2 border-nps-oracle-accent border-t-transparent rounded-full animate-spin" />
        {t("common.loading")}
      </div>
    );
  }

  const selectedIds = new Set<number>();
  if (selectedUsers) {
    selectedIds.add(selectedUsers.primary.id);
    selectedUsers.secondary.forEach((u) => selectedIds.add(u.id));
  }

  const totalSelected = selectedIds.size;

  function handlePrimaryChange(userId: number | null) {
    setError(null);
    if (userId === null) {
      onChange(null);
      return;
    }
    const user = users.find((u) => u.id === userId);
    if (!user) return;

    // If switching primary and old primary was in secondary, remove it
    const newSecondary = selectedUsers
      ? selectedUsers.secondary.filter((u) => u.id !== userId)
      : [];

    onChange({ primary: user, secondary: newSecondary });
  }

  function handleAddSecondary(userId: number) {
    setError(null);
    if (!selectedUsers) return;

    if (selectedIds.has(userId)) {
      setError(t("oracle.duplicate_user_error"));
      return;
    }

    if (totalSelected >= MAX_TOTAL_USERS) {
      setError(t("oracle.max_users_error"));
      return;
    }

    const user = users.find((u) => u.id === userId);
    if (!user) return;

    onChange({
      ...selectedUsers,
      secondary: [...selectedUsers.secondary, user],
    });
    setShowSecondaryDropdown(false);
  }

  function handleRemoveSecondary(userId: number) {
    if (!selectedUsers) return;
    setError(null);
    onChange({
      ...selectedUsers,
      secondary: selectedUsers.secondary.filter((u) => u.id !== userId),
    });
  }

  // Users available for secondary selection (exclude already selected)
  const availableForSecondary = users.filter((u) => !selectedIds.has(u.id));

  return (
    <div className="space-y-3">
      {/* Primary user selector */}
      <div>
        <label className="block text-xs text-nps-text-dim mb-1">
          {t("oracle.primary_user")}
        </label>
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={selectedUsers?.primary.id ?? ""}
            onChange={(e) => {
              const val = e.target.value;
              handlePrimaryChange(val ? Number(val) : null);
            }}
            className="bg-nps-bg-input border border-nps-oracle-border text-nps-text rounded px-3 py-2 text-sm min-w-[200px] focus:outline-none focus:border-nps-oracle-accent"
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
            onClick={onAddNew}
            className="px-3 py-2 text-sm bg-nps-oracle-accent/20 text-nps-oracle-accent border border-nps-oracle-border rounded hover:bg-nps-oracle-accent/30 transition-colors"
          >
            + {t("oracle.add_new_profile")}
          </button>

          {selectedUsers && (
            <button
              onClick={onEdit}
              className="px-3 py-2 text-sm text-nps-text-dim border border-nps-border rounded hover:text-nps-text hover:border-nps-oracle-border transition-colors"
            >
              {t("oracle.edit_profile")}
            </button>
          )}
        </div>
      </div>

      {/* Selected users chips + add secondary */}
      {selectedUsers && (
        <div>
          <label className="block text-xs text-nps-text-dim mb-1">
            {t("oracle.secondary_users")}
          </label>
          <div className="flex items-center gap-2 flex-wrap">
            <UserChip name={selectedUsers.primary.name} isPrimary />
            {selectedUsers.secondary.map((user) => (
              <UserChip
                key={user.id}
                name={user.name}
                onRemove={() => handleRemoveSecondary(user.id)}
              />
            ))}

            {/* Add secondary user */}
            {totalSelected < MAX_TOTAL_USERS &&
              availableForSecondary.length > 0 && (
                <div className="relative">
                  {showSecondaryDropdown ? (
                    <select
                      autoFocus
                      value=""
                      onChange={(e) => {
                        if (e.target.value) {
                          handleAddSecondary(Number(e.target.value));
                        }
                      }}
                      onBlur={() => setShowSecondaryDropdown(false)}
                      className="bg-nps-bg-input border border-nps-oracle-border text-nps-text rounded px-2 py-1 text-xs focus:outline-none focus:border-nps-oracle-accent"
                    >
                      <option value="">{t("oracle.select_profile")}</option>
                      {availableForSecondary.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <button
                      onClick={() => setShowSecondaryDropdown(true)}
                      className="px-2 py-1 text-xs bg-nps-bg-hover text-nps-text-dim border border-dashed border-nps-border rounded hover:border-nps-oracle-accent hover:text-nps-oracle-accent transition-colors"
                    >
                      + {t("oracle.add_secondary")}
                    </button>
                  )}
                </div>
              )}
          </div>
        </div>
      )}

      {/* Error message */}
      {error && <p className="text-xs text-nps-bg-danger">{error}</p>}
    </div>
  );
}
