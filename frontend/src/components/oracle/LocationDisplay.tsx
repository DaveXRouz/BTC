import { useTranslation } from "react-i18next";
import type { LocationElementData } from "@/types";

interface LocationDisplayProps {
  location: LocationElementData | null;
}

const ELEMENT_COLORS: Record<string, string> = {
  Wood: "text-green-500 bg-green-500/10 border-green-500/30",
  Fire: "text-red-500 bg-red-500/10 border-red-500/30",
  Earth: "text-amber-700 bg-amber-700/10 border-amber-700/30",
  Metal: "text-gray-400 bg-gray-400/10 border-gray-400/30",
  Water: "text-blue-500 bg-blue-500/10 border-blue-500/30",
};

function formatOffset(tz: number): string {
  const sign = tz >= 0 ? "+" : "";
  return `${sign}${tz}`;
}

export function LocationDisplay({ location }: LocationDisplayProps) {
  const { t } = useTranslation();

  if (!location) {
    return (
      <div
        className="text-xs text-nps-text-dim italic py-2"
        data-testid="location-empty"
      >
        {t("oracle.location_display_empty")}
      </div>
    );
  }

  const colorClass =
    ELEMENT_COLORS[location.element] ??
    "text-nps-text-dim bg-nps-bg-input border-nps-border";

  return (
    <div className="space-y-2" data-testid="location-display">
      {/* Element badge */}
      <div className="flex items-center gap-2">
        <span
          className={`text-xs px-2 py-0.5 rounded border ${colorClass}`}
          data-testid="location-element"
        >
          {t("oracle.location_display_element", { element: location.element })}
        </span>
      </div>

      {/* Hemisphere */}
      <div className="flex items-center gap-3 text-xs text-nps-text-dim">
        <span data-testid="location-hemisphere">
          {t("oracle.location_display_hemisphere", {
            lat_hem: location.lat_hemisphere,
            lon_hem: location.lon_hemisphere,
          })}
        </span>

        {/* Polarity */}
        <span data-testid="location-polarity">
          {t("oracle.location_display_polarity", {
            lat_pol: location.lat_polarity,
            lon_pol: location.lon_polarity,
          })}
        </span>

        {/* Timezone */}
        <span data-testid="location-timezone">
          {t("oracle.location_display_timezone", {
            offset: formatOffset(location.timezone_estimate),
          })}
        </span>
      </div>
    </div>
  );
}
