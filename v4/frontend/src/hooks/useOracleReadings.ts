import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { oracle } from "@/services/api";

const HISTORY_KEY = ["oracleReadings"] as const;

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
    mutationFn: (question: string) => oracle.question(question),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useSubmitName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => oracle.name(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useReadingHistory(params?: {
  limit?: number;
  offset?: number;
  sign_type?: string;
}) {
  return useQuery({
    queryKey: [...HISTORY_KEY, params],
    queryFn: () => oracle.history(params),
  });
}
