import { useTranslation } from "react-i18next";
import { toPersianDigits } from "@/utils/persianDigits";

interface NumerologyNumberDisplayProps {
  number: number;
  label: string;
  meaning: string;
  size?: "sm" | "md" | "lg";
}

const MASTER_NUMBERS = [11, 22, 33];

const SIZE_CLASSES: Record<
  string,
  { number: string; label: string; meaning: string }
> = {
  sm: { number: "text-2xl", label: "text-xs", meaning: "text-xs" },
  md: { number: "text-4xl", label: "text-xs", meaning: "text-sm" },
  lg: { number: "text-5xl", label: "text-sm", meaning: "text-base" },
};

export function NumerologyNumberDisplay({
  number,
  label,
  meaning,
  size = "md",
}: NumerologyNumberDisplayProps) {
  const { i18n } = useTranslation();
  const isMaster = MASTER_NUMBERS.includes(number);
  const displayNumber =
    i18n.language === "fa" ? toPersianDigits(number) : String(number);
  const sizeClasses = SIZE_CLASSES[size];

  return (
    <div className="flex flex-col items-center text-center">
      <span
        className={`${sizeClasses.label} text-nps-text-dim uppercase tracking-wide`}
      >
        {label}
      </span>
      <span
        className={`${sizeClasses.number} font-mono font-bold ${
          isMaster ? "text-nps-score-peak" : "text-nps-text-bright"
        }`}
        data-testid="numerology-number"
      >
        {displayNumber}
      </span>
      <span className={`${sizeClasses.meaning} text-nps-text-dim mt-1`}>
        {meaning}
      </span>
      {isMaster && (
        <span
          className="text-xs text-nps-score-peak mt-0.5"
          data-testid="master-badge"
        >
          Master Number
        </span>
      )}
    </div>
  );
}
