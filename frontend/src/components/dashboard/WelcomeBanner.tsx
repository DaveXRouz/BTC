import { useTranslation } from "react-i18next";
import { MoonPhaseWidget } from "./MoonPhaseWidget";
import { toJalaali } from "jalaali-js";

interface MoonPhaseInfo {
  phase_name: string;
  illumination: number;
  emoji: string;
}

interface WelcomeBannerProps {
  userName?: string;
  moonData?: MoonPhaseInfo | null;
  isLoading?: boolean;
}

function getGreetingKey(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "dashboard.welcome_morning";
  if (hour < 18) return "dashboard.welcome_afternoon";
  return "dashboard.welcome_evening";
}

function formatDate(locale: string): string {
  const now = new Date();
  if (locale === "fa") {
    const jDate = toJalaali(
      now.getFullYear(),
      now.getMonth() + 1,
      now.getDate(),
    );
    return `${jDate.jy}/${String(jDate.jm).padStart(2, "0")}/${String(jDate.jd).padStart(2, "0")}`;
  }
  return now.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function WelcomeBanner({
  userName,
  moonData,
  isLoading,
}: WelcomeBannerProps) {
  const { t, i18n } = useTranslation();

  const greeting = t(getGreetingKey());
  const welcomeText = userName
    ? t("dashboard.welcome_user", { greeting, name: userName })
    : t("dashboard.welcome_explorer", { greeting });
  const dateText = t("dashboard.today_date", {
    date: formatDate(i18n.language),
  });

  return (
    <div
      className="bg-nps-oracle-bg rounded-xl p-6 flex items-center justify-between"
      data-testid="welcome-banner"
    >
      <div>
        <h1 className="text-xl font-bold text-nps-text-bright">
          {welcomeText}
        </h1>
        <p className="text-sm text-nps-text-dim mt-1">{dateText}</p>
      </div>
      <MoonPhaseWidget moonData={moonData} isLoading={isLoading} />
    </div>
  );
}
