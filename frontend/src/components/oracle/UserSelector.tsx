import type { OracleUser } from "@/types";
import { useTranslation } from "react-i18next";

interface UserSelectorProps {
  users: OracleUser[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onAddNew: () => void;
  onEdit: () => void;
  isLoading?: boolean;
}

export function UserSelector({
  users,
  selectedId,
  onSelect,
  onAddNew,
  onEdit,
  isLoading,
}: UserSelectorProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-nps-text-dim text-sm">
        <div className="h-4 w-4 border-2 border-nps-oracle-accent border-t-transparent rounded-full animate-spin" />
        {t("common.loading")}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <select
        value={selectedId ?? ""}
        onChange={(e) => {
          const val = e.target.value;
          onSelect(val ? Number(val) : null);
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

      {selectedId !== null && (
        <button
          onClick={onEdit}
          className="px-3 py-2 text-sm text-nps-text-dim border border-nps-border rounded hover:text-nps-text hover:border-nps-oracle-border transition-colors"
        >
          {t("oracle.edit_profile")}
        </button>
      )}
    </div>
  );
}
