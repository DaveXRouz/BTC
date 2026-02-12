import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

interface DailyInsightResponse {
  date: string;
  summary: string;
  fc60_stamp?: string;
  moon_phase?: string;
  energy_level?: number;
  advice?: string[];
}

interface DailyReadingCardProps {
  dailyReading?: DailyInsightResponse | null;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

export function DailyReadingCard({
  dailyReading,
  isLoading,
  isError,
  onRetry,
}: DailyReadingCardProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div
        className="bg-nps-bg-card border border-nps-border rounded-xl p-6 animate-pulse"
        data-testid="daily-loading"
      >
        <div className="h-5 w-40 bg-nps-bg-elevated rounded mb-3" />
        <div className="h-4 w-full bg-nps-bg-elevated rounded mb-2" />
        <div className="h-4 w-2/3 bg-nps-bg-elevated rounded" />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className="bg-nps-bg-card border border-nps-error/30 rounded-xl p-6"
        data-testid="daily-error"
      >
        <h2 className="text-lg font-semibold text-nps-text-bright">
          {t("dashboard.daily_reading")}
        </h2>
        <p className="text-sm text-nps-text-dim mt-2">
          {t("dashboard.daily_error")}
        </p>
        <button
          onClick={onRetry}
          className="mt-3 px-4 py-2 text-sm rounded-lg bg-nps-oracle-accent text-white hover:opacity-90 transition-opacity"
        >
          {t("dashboard.daily_retry")}
        </button>
      </div>
    );
  }

  if (!dailyReading) {
    return (
      <div
        className="bg-nps-bg-card border border-nps-oracle-border rounded-xl p-6"
        data-testid="daily-empty"
      >
        <h2 className="text-lg font-semibold text-nps-text-bright">
          {t("dashboard.daily_reading")}
        </h2>
        <p className="text-sm text-nps-text-dim mt-2">
          {t("dashboard.daily_no_reading")}
        </p>
        <button
          onClick={() => navigate("/oracle?type=daily")}
          className="mt-3 px-4 py-2 text-sm rounded-lg bg-nps-success text-white hover:opacity-90 transition-opacity animate-pulse"
          data-testid="generate-daily-btn"
        >
          {t("dashboard.daily_generate")}
        </button>
      </div>
    );
  }

  return (
    <div
      className="bg-nps-bg-card border border-nps-oracle-border rounded-xl p-6"
      data-testid="daily-card"
    >
      <h2 className="text-lg font-semibold text-nps-text-bright">
        {t("dashboard.daily_reading")}
      </h2>
      <p className="text-sm text-nps-text mt-2">{dailyReading.summary}</p>
      {dailyReading.fc60_stamp && (
        <p className="text-xs text-nps-text-dim mt-2 font-mono">
          {dailyReading.fc60_stamp}
        </p>
      )}
      {dailyReading.advice && dailyReading.advice.length > 0 && (
        <ul className="mt-2 space-y-1">
          {dailyReading.advice.map((item, i) => (
            <li key={i} className="text-sm text-nps-text-dim">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
