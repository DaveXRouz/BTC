import { useTranslation } from "react-i18next";
import type { SignData, SignType } from "@/types";

interface SignTypeSelectorProps {
  value: SignData;
  onChange: (data: SignData) => void;
  error?: string;
}

const SIGN_TYPES: SignType[] = ["time", "number", "carplate", "custom"];

export function SignTypeSelector({
  value,
  onChange,
  error,
}: SignTypeSelectorProps) {
  const { t } = useTranslation();

  function handleTypeChange(newType: SignType) {
    onChange({ type: newType, value: "" });
  }

  function handleValueChange(newValue: string) {
    onChange({ type: value.type, value: newValue });
  }

  return (
    <div>
      <label className="block text-sm text-nps-text-dim mb-1">
        {t("oracle.sign_label")}
        <span className="text-nps-error ms-1">*</span>
      </label>

      {/* Type selector */}
      <select
        value={value.type}
        onChange={(e) => handleTypeChange(e.target.value as SignType)}
        className="w-full bg-nps-bg-input border border-nps-border rounded px-3 py-2 min-h-[44px] sm:min-h-0 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent mb-2"
        aria-label={t("oracle.sign_type_label")}
      >
        {SIGN_TYPES.map((st) => (
          <option key={st} value={st}>
            {t(`oracle.sign_type_${st}`)}
          </option>
        ))}
      </select>

      {/* Conditional input */}
      {value.type === "time" && (
        <input
          type="time"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value)}
          className={`w-full bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
            error ? "border-nps-error" : "border-nps-border"
          }`}
          aria-label={t("oracle.sign_type_time")}
        />
      )}

      {value.type === "number" && (
        <input
          type="text"
          inputMode="numeric"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value)}
          placeholder={t("oracle.sign_placeholder_number")}
          className={`w-full bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
            error ? "border-nps-error" : "border-nps-border"
          }`}
          aria-label={t("oracle.sign_type_number")}
        />
      )}

      {value.type === "carplate" && (
        <input
          type="text"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value.toUpperCase())}
          placeholder={t("oracle.sign_placeholder_carplate")}
          className={`w-full bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
            error ? "border-nps-error" : "border-nps-border"
          }`}
          aria-label={t("oracle.sign_type_carplate")}
        />
      )}

      {value.type === "custom" && (
        <input
          type="text"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value)}
          placeholder={t("oracle.sign_placeholder_custom")}
          className={`w-full bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
            error ? "border-nps-error" : "border-nps-border"
          }`}
          aria-label={t("oracle.sign_type_custom")}
        />
      )}

      {error && <p className="text-nps-error text-xs mt-1">{error}</p>}
    </div>
  );
}
