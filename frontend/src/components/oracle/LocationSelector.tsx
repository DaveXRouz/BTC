import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { LocationData } from "@/types";
import { getCurrentPosition, COUNTRIES } from "@/utils/geolocationHelpers";

interface LocationSelectorProps {
  value: LocationData | null;
  onChange: (data: LocationData) => void;
}

export function LocationSelector({ value, onChange }: LocationSelectorProps) {
  const { t } = useTranslation();
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectError, setDetectError] = useState<string | null>(null);

  async function handleAutoDetect() {
    setIsDetecting(true);
    setDetectError(null);
    try {
      const coords = await getCurrentPosition();
      onChange({ ...coords, country: undefined, city: undefined });
    } catch {
      setDetectError(t("oracle.location_detect_error"));
    } finally {
      setIsDetecting(false);
    }
  }

  function handleCountryChange(country: string) {
    if (!country) return;
    const loc = COUNTRIES[country];
    if (loc) {
      onChange({ ...loc });
    }
  }

  function handleCityChange(city: string) {
    if (value) {
      onChange({ ...value, city });
    }
  }

  const countryNames = Object.keys(COUNTRIES);

  return (
    <div>
      <label className="block text-sm text-nps-text-dim mb-1">
        {t("oracle.location_label")}
      </label>

      {/* Auto-detect button */}
      <button
        type="button"
        onClick={handleAutoDetect}
        disabled={isDetecting}
        className="mb-2 px-3 py-2 text-sm bg-nps-oracle-accent/20 text-nps-oracle-accent border border-nps-oracle-border rounded hover:bg-nps-oracle-accent/30 transition-colors disabled:opacity-50"
      >
        {isDetecting ? (
          <span className="flex items-center gap-2">
            <span className="h-3 w-3 border-2 border-nps-oracle-accent border-t-transparent rounded-full animate-spin" />
            {t("oracle.location_detecting")}
          </span>
        ) : (
          t("oracle.location_auto_detect")
        )}
      </button>

      {detectError && (
        <p className="text-nps-error text-xs mb-2">{detectError}</p>
      )}

      {/* Manual selection */}
      <div className="flex gap-2">
        <select
          value={value?.country ?? ""}
          onChange={(e) => handleCountryChange(e.target.value)}
          className="flex-1 bg-nps-bg-input border border-nps-border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent"
          aria-label={t("oracle.location_country")}
        >
          <option value="">{t("oracle.location_country")}</option>
          {countryNames.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <input
          type="text"
          value={value?.city ?? ""}
          onChange={(e) => handleCityChange(e.target.value)}
          placeholder={t("oracle.location_city")}
          className="flex-1 bg-nps-bg-input border border-nps-border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent"
          aria-label={t("oracle.location_city")}
        />
      </div>

      {/* Coordinates display */}
      {value && (
        <p className="text-xs text-nps-text-dim mt-1 font-mono">
          {t("oracle.location_coordinates")}: {value.lat}, {value.lon}
        </p>
      )}
    </div>
  );
}
