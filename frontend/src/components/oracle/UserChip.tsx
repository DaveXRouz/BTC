import { useTranslation } from "react-i18next";

interface UserChipProps {
  name: string;
  isPrimary?: boolean;
  onRemove?: () => void;
}

export function UserChip({ name, isPrimary, onRemove }: UserChipProps) {
  const { t } = useTranslation();

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs ${
        isPrimary
          ? "bg-nps-oracle-accent/20 text-nps-oracle-accent border border-nps-oracle-accent font-bold"
          : "bg-nps-bg-input text-nps-text border border-nps-border"
      }`}
    >
      {name}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-1 hover:text-nps-bg-danger transition-colors"
          aria-label={`${t("oracle.remove_user")} ${name}`}
        >
          &times;
        </button>
      )}
    </span>
  );
}
