import { useQuery } from "@tanstack/react-query";
import { dashboard, oracle } from "@/services/api";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboardStats"],
    queryFn: () => dashboard.stats(),
    refetchInterval: 60_000,
  });
}

export function useRecentReadings(limit = 5) {
  return useQuery({
    queryKey: ["recentReadings", limit],
    queryFn: () => oracle.history({ limit }),
  });
}

export function useDailyReading(date?: string) {
  return useQuery({
    queryKey: ["dailyReading", date],
    queryFn: () => oracle.daily(date),
  });
}
