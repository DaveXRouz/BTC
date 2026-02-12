import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { oracle } from "@/services/api";
import type { ReadingSearchParams } from "@/types";

const HISTORY_KEY = ["oracleReadings"] as const;
const STATS_KEY = ["readingStats"] as const;

export function useSubmitReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datetime?: string) => oracle.reading(datetime),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useSubmitQuestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      question: string;
      userId?: number;
      system?: string;
    }) => oracle.question(params.question, params.userId, params.system),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useSubmitName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { name: string; userId?: number; system?: string }) =>
      oracle.name(params.name, params.userId, params.system),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useSubmitTimeReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: import("@/types").TimeReadingRequest) =>
      oracle.timeReading(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useDailyReading(userId: number | null, date?: string) {
  return useQuery({
    queryKey: ["dailyReading", userId, date],
    queryFn: () => oracle.getDailyReading(userId!, date),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 min — daily readings don't change often
  });
}

export function useGenerateDailyReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: import("@/types").DailyReadingRequest) =>
      oracle.dailyReading(data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({
        queryKey: ["dailyReading", variables.user_id],
      });
      qc.invalidateQueries({ queryKey: HISTORY_KEY });
    },
  });
}

export function useSubmitMultiUserReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: import("@/types").MultiUserFrameworkRequest) =>
      oracle.multiUserFrameworkReading(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useReadingHistory(params?: ReadingSearchParams) {
  return useQuery({
    queryKey: [...HISTORY_KEY, params],
    queryFn: () => oracle.history(params),
  });
}

export function useDeleteReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => oracle.deleteReading(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: HISTORY_KEY });
      qc.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useToggleFavorite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => oracle.toggleFavorite(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: HISTORY_KEY });
      qc.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useReadingStats() {
  return useQuery({
    queryKey: [...STATS_KEY],
    queryFn: () => oracle.readingStats(),
    staleTime: 60 * 1000, // 1 min
  });
}
