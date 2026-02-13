import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { admin as api } from "@/services/api";
import type { UserSortField, SortOrder, ProfileSortField } from "@/types";

const USERS_KEY = ["admin", "users"] as const;
const PROFILES_KEY = ["admin", "profiles"] as const;
const STATS_KEY = ["admin", "stats"] as const;

export function useAdminUsers(params?: {
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: UserSortField;
  sort_order?: SortOrder;
}) {
  return useQuery({
    queryKey: [...USERS_KEY, params],
    queryFn: () => api.listUsers(params),
  });
}

export function useAdminUser(id: string | null) {
  return useQuery({
    queryKey: [...USERS_KEY, id],
    queryFn: () => api.getUser(id!),
    enabled: id !== null,
  });
}

export function useUpdateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      api.updateRole(id, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: USERS_KEY }),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (id: string) => api.resetPassword(id),
  });
}

export function useUpdateStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.updateStatus(id, is_active),
    onSuccess: () => qc.invalidateQueries({ queryKey: USERS_KEY }),
  });
}

export function useAdminStats() {
  return useQuery({
    queryKey: STATS_KEY,
    queryFn: () => api.stats(),
  });
}

export function useAdminProfiles(params?: {
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: ProfileSortField;
  sort_order?: SortOrder;
  include_deleted?: boolean;
}) {
  return useQuery({
    queryKey: [...PROFILES_KEY, params],
    queryFn: () => api.listProfiles(params),
  });
}

export function useDeleteProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteProfile(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: PROFILES_KEY }),
  });
}
