import { useTranslation } from "react-i18next";
import type { GanzhiFullData } from "@/types";

interface GanzhiDisplayProps {
  ganzhi: GanzhiFullData;
  compact?: boolean;
}

const ELEMENT_COLORS: Record<string, string> = {
  Wood: "bg-green-500",
  Fire: "bg-red-500",
  Earth: "bg-amber-600",
  Metal: "bg-gray-400",
  Water: "bg-blue-500",
};

export default function GanzhiDisplay({
  ganzhi,
  compact = false,
}: GanzhiDisplayProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-3">
      {/* Year Cycle */}
      {ganzhi.year && (
        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
            {t("oracle.cosmic.year_cycle")}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold">{ganzhi.year.animal_name}</span>
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs font-semibold text-white ${ELEMENT_COLORS[ganzhi.year.element] || "bg-gray-400"}`}
            >
              {ganzhi.year.element}
            </span>
            <span className="text-sm text-gray-500">
              {ganzhi.year.polarity === "Yang" ? "\u2600" : "\uD83C\uDF19"}{" "}
              {ganzhi.year.polarity}
            </span>
          </div>
          {ganzhi.year.traditional_name && (
            <div className="text-sm text-gray-600">
              {ganzhi.year.traditional_name}
            </div>
          )}
          {ganzhi.year.gz_token && (
            <div className="text-xs font-mono text-gray-400">
              {ganzhi.year.gz_token}
            </div>
          )}
        </div>
      )}

      {/* Day Cycle */}
      {!compact && ganzhi.day && (
        <>
          <hr className="border-gray-200" />
          <div>
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              {t("oracle.cosmic.day_cycle")}
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">{ganzhi.day.animal_name}</span>
              <span
                className={`inline-block px-1.5 py-0.5 rounded text-xs font-semibold text-white ${ELEMENT_COLORS[ganzhi.day.element] || "bg-gray-400"}`}
              >
                {ganzhi.day.element}
              </span>
              <span className="text-xs text-gray-500">
                {ganzhi.day.polarity}
              </span>
            </div>
            {ganzhi.day.gz_token && (
              <div className="text-xs font-mono text-gray-400">
                {ganzhi.day.gz_token}
              </div>
            )}
          </div>
        </>
      )}

      {/* Hour Cycle (conditional) */}
      {!compact && ganzhi.hour && (
        <>
          <hr className="border-gray-200" />
          <div>
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              {t("oracle.cosmic.hour_cycle")}
            </div>
            <span className="text-sm font-medium">
              {ganzhi.hour.animal_name}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
