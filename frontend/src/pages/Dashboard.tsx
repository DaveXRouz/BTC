import { useTranslation } from "react-i18next";
import { WelcomeBanner } from "@/components/dashboard/WelcomeBanner";
import { DailyReadingCard } from "@/components/dashboard/DailyReadingCard";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { RecentReadings } from "@/components/dashboard/RecentReadings";
import { QuickActions } from "@/components/dashboard/QuickActions";
import {
  useDashboardStats,
  useRecentReadings,
  useDailyReading,
} from "@/hooks/useDashboard";

export default function Dashboard() {
  const { t } = useTranslation();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: recent, isLoading: recentLoading } = useRecentReadings();
  const {
    data: daily,
    isLoading: dailyLoading,
    isError: dailyError,
    refetch: retryDaily,
  } = useDailyReading();

  return (
    <div className="space-y-6">
      <h2 className="sr-only">{t("dashboard.title")}</h2>
      <WelcomeBanner isLoading={dailyLoading} />
      <DailyReadingCard
        dailyReading={
          daily
            ? {
                date: String((daily as Record<string, unknown>).date ?? ""),
                summary: String(
                  (daily as Record<string, unknown>).summary ?? "",
                ),
                fc60_stamp: (daily as Record<string, unknown>).fc60_stamp as
                  | string
                  | undefined,
                advice: (daily as Record<string, unknown>).advice as
                  | string[]
                  | undefined,
              }
            : null
        }
        isLoading={dailyLoading}
        isError={dailyError}
        onRetry={() => retryDaily()}
      />
      <StatsCards stats={stats} isLoading={statsLoading} />
      <RecentReadings
        readings={recent?.readings ?? []}
        isLoading={recentLoading}
        isError={false}
        total={recent?.total ?? 0}
      />
      <QuickActions />
    </div>
  );
}
