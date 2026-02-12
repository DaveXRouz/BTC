import { useTranslation } from "react-i18next";
import type { CosmicCycleData } from "@/types";
import MoonPhaseDisplay from "./MoonPhaseDisplay";
import GanzhiDisplay from "./GanzhiDisplay";

interface CosmicCyclePanelProps {
  cosmicData: CosmicCycleData;
  compact?: boolean;
}

export default function CosmicCyclePanel({
  cosmicData,
  compact = false,
}: CosmicCyclePanelProps) {
  const { t } = useTranslation();

  const hasMoon = cosmicData.moon !== null;
  const hasGanzhi = cosmicData.ganzhi !== null;
  const hasCurrent = cosmicData.current !== null;
  const hasPlanetMoon = cosmicData.planet_moon !== null;
  const hasAnyData = hasMoon || hasGanzhi || hasCurrent;

  if (!hasAnyData) {
    return (
      <div className="text-center text-gray-500 py-8">
        {t("oracle.cosmic.no_data")}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">{t("oracle.cosmic.title")}</h3>

      <div
        className={
          compact ? "space-y-4" : "grid grid-cols-1 md:grid-cols-3 gap-4"
        }
      >
        {/* Moon Section */}
        {hasMoon && (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              {t("oracle.cosmic.moon_title")}
            </h4>
            <MoonPhaseDisplay moon={cosmicData.moon!} compact={compact} />
          </div>
        )}

        {/* Ganzhi Section */}
        {hasGanzhi && (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              {t("oracle.cosmic.ganzhi_title")}
            </h4>
            <GanzhiDisplay ganzhi={cosmicData.ganzhi!} compact={compact} />
          </div>
        )}

        {/* Current Moment + Planet-Moon Section */}
        {(hasCurrent || hasPlanetMoon) && (
          <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
            {hasCurrent && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">
                  {t("oracle.cosmic.current_title")}
                </h4>
                <div className="text-sm space-y-1">
                  <div>
                    <span className="text-gray-500">
                      {t("oracle.cosmic.ruling_planet")}:{" "}
                    </span>
                    <span className="font-medium">
                      {cosmicData.current!.planet}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">
                      {t("oracle.cosmic.domain")}:{" "}
                    </span>
                    <span>{cosmicData.current!.domain}</span>
                  </div>
                </div>
              </div>
            )}

            {hasPlanetMoon && (
              <div className="bg-indigo-50 rounded-md p-3">
                <h4 className="text-sm font-semibold text-indigo-700 mb-1">
                  {t("oracle.cosmic.planet_moon_title")}
                </h4>
                <div className="text-sm font-medium text-indigo-900">
                  {cosmicData.planet_moon!.theme}
                </div>
                <p className="text-xs text-indigo-700 mt-1">
                  {cosmicData.planet_moon!.message}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
