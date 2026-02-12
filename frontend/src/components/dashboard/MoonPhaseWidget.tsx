import { useTranslation } from "react-i18next";

interface MoonPhaseInfo {
  phase_name: string;
  illumination: number;
  emoji: string;
}

interface MoonPhaseWidgetProps {
  moonData?: MoonPhaseInfo | null;
  isLoading?: boolean;
}

export function MoonPhaseWidget({ moonData, isLoading }: MoonPhaseWidgetProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div
        className="flex items-center gap-2 animate-pulse"
        data-testid="moon-loading"
      >
        <div className="w-6 h-6 rounded-full bg-nps-bg-elevated" />
        <div className="h-4 w-20 rounded bg-nps-bg-elevated" />
      </div>
    );
  }

  if (!moonData) return null;

  return (
    <div className="flex items-center gap-2" data-testid="moon-widget">
      <span className="text-xl" role="img" aria-label={moonData.phase_name}>
        {moonData.emoji}
      </span>
      <div className="text-sm">
        <span className="text-nps-text-bright">{moonData.phase_name}</span>
        <span className="text-nps-text-dim ml-2">
          {t("dashboard.moon_illumination", {
            percent: Math.round(moonData.illumination * 100),
          })}
        </span>
      </div>
    </div>
  );
}
