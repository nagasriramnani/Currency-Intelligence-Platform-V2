/**
 * React Query hooks for fetching currency data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export function useLatestRates(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['latestRates', startDate, endDate],
    queryFn: () => apiClient.getLatestRates(startDate, endDate),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data stale after 30 seconds
    enabled: typeof window !== 'undefined',
  });
}

export function useTimeSeriesData(
  currencies?: string[],
  startDate?: string | null,
  endDate?: string | null
) {
  return useQuery({
    queryKey: ['timeSeries', currencies, startDate, endDate],
    queryFn: () => apiClient.getTimeSeriesData(currencies, startDate ?? undefined, endDate ?? undefined),
    staleTime: 60000,
    enabled: typeof window !== 'undefined',
  });
}

export function useYoYComparison(startDate?: string | null, endDate?: string | null) {
  return useQuery({
    queryKey: ['yoyComparison', startDate, endDate],
    queryFn: () => apiClient.getYoYComparison(startDate ?? undefined, endDate ?? undefined),
    staleTime: 60000,
    enabled: typeof window !== 'undefined',
  });
}

export function useVolatilitySummary() {
  return useQuery({
    queryKey: ['volatilitySummary'],
    queryFn: () => apiClient.getVolatilitySummary(),
    staleTime: 60000,
    enabled: typeof window !== 'undefined',
  });
}

export function useVolatilityTimeSeries(currency: string) {
  return useQuery({
    queryKey: ['volatilityTimeSeries', currency],
    queryFn: () => apiClient.getVolatilityTimeSeries(currency),
    enabled: !!currency && typeof window !== 'undefined',
    staleTime: 60000,
  });
}

export function useForecast(
  currency: string,
  horizon: number = 6,
  startDate?: string | null,
  endDate?: string | null
) {
  return useQuery({
    queryKey: ['forecast', currency, horizon, startDate, endDate],
    queryFn: () => apiClient.getForecast(currency, horizon, startDate ?? undefined, endDate ?? undefined),
    enabled: !!currency && typeof window !== 'undefined',
    staleTime: 300000, // 5 minutes
  });
}

export function useAnomalies(currency?: string, startDate?: string | null, endDate?: string | null) {
  return useQuery({
    queryKey: ['anomalies', currency, startDate, endDate],
    queryFn: () => apiClient.getAnomalies(currency, startDate ?? undefined, endDate ?? undefined),
    staleTime: 60000,
    enabled: typeof window !== 'undefined',
  });
}

export function useInsights(currency: string) {
  return useQuery({
    queryKey: ['insights', currency],
    queryFn: () => apiClient.getInsights(currency),
    enabled: !!currency && typeof window !== 'undefined',
    staleTime: 300000,
  });
}

export function useSummaryInsight() {
  return useQuery({
    queryKey: ['summaryInsight'],
    queryFn: () => apiClient.getSummaryInsight(),
    staleTime: 300000,
    enabled: typeof window !== 'undefined',
  });
}

export function useHighlights(startDate?: string | null, endDate?: string | null) {
  return useQuery({
    queryKey: ['highlights', startDate, endDate],
    queryFn: () => apiClient.getHighlights(startDate ?? undefined, endDate ?? undefined),
    staleTime: 300000,
    enabled: typeof window !== 'undefined',
  });
}

export function useAlertHistory(limit: number = 10) {
  return useQuery({
    queryKey: ['alertHistory', limit],
    queryFn: () => apiClient.getAlertHistory(limit),
    staleTime: 10000,
    refetchInterval: 30000, // Refetch every 30 seconds
    enabled: typeof window !== 'undefined',
  });
}

export function useTestAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.sendTestAlert(),
    onSuccess: () => {
      // Invalidate alert history to refresh
      queryClient.invalidateQueries({ queryKey: ['alertHistory'] });
    },
  });
}

export function useCheckAlerts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.checkAlerts(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertHistory'] });
    },
  });
}

export function useSlackSummary() {
  return useMutation({
    mutationFn: (range: { start_date?: string | null; end_date?: string | null }) =>
      apiClient.sendSlackSummary(range),
  });
}

export function useRefreshData() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (daysBack?: number) => apiClient.refreshData(daysBack),
    onSuccess: () => {
      // Invalidate all queries to force refresh
      queryClient.invalidateQueries();
    },
  });
}

