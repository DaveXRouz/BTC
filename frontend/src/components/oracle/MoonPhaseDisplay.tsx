import { useTranslation } from "react-i18next";
import type { MoonPhaseData } from "@/types";

interface MoonPhaseDisplayProps {
  moon: MoonPhaseData;
  compact?: boolean;
}

const ENERGY_COLORS: Record<string, string> = {
  Seed: "bg-green-100 text-green-800",
  Build: "bg-blue-100 text-blue-800",
  Challenge: "bg-red-100 text-red-800",
  Refine: "bg-purple-100 text-purple-800",
  Culminate: "bg-yellow-100 text-yellow-800",
  Share: "bg-teal-100 text-teal-800",
  Release: "bg-orange-100 text-orange-800",
  Rest: "bg-gray-100 text-gray-800",
};

export default function MoonPhaseDisplay({
  moon,
  compact = false,
}: MoonPhaseDisplayProps) {
  const { t } = useTranslation();
  const illumination = Math.max(0, Math.min(100, moon.illumination));
  const energyColor = ENERGY_COLORS[moon.energy] || "bg-gray-100 text-gray-800";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-3xl" role="img" aria-label={moon.phase_name}>
          {moon.emoji}
        </span>
        <span className="text-lg font-semibold">{moon.phase_name}</span>
      </div>

      <div>
        <div className="flex items-center justify-between text-sm mb-1">
          <span>{t("oracle.cosmic.illumination")}</span>
          <span>{illumination.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-yellow-300 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${illumination}%` }}
            role="progressbar"
            aria-valuenow={illumination}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {t("oracle.cosmic.moon_age")}: {moon.age.toFixed(2)}{" "}
          {t("oracle.cosmic.days")}
        </div>
      </div>

      {moon.energy && (
        <div>
          <span className="text-sm font-medium">
            {t("oracle.cosmic.energy")}:{" "}
          </span>
          <span
            className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${energyColor}`}
          >
            {moon.energy}
          </span>
        </div>
      )}

      {!compact && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          {moon.best_for && (
            <div>
              <div className="flex items-center gap-1 font-medium text-green-700">
                <span>&#10003;</span>
                <span>{t("oracle.cosmic.best_for")}</span>
              </div>
              <p className="text-gray-600 mt-0.5">{moon.best_for}</p>
            </div>
          )}
          {moon.avoid && (
            <div>
              <div className="flex items-center gap-1 font-medium text-amber-700">
                <span>&#9888;</span>
                <span>{t("oracle.cosmic.avoid")}</span>
              </div>
              <p className="text-gray-600 mt-0.5">{moon.avoid}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
