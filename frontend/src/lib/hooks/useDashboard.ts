'use client';

import { useState, useEffect, useCallback } from 'react';
import { get } from '@/lib/api';
import type { DashboardData } from '@/types';

interface UseDashboardReturn {
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useDashboard(): UseDashboardReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await get<DashboardData>('/dashboard/');
      setData(response);
    } catch (err) {
      // Error is handled by API client interceptor (redirects to login on 401)
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load dashboard data');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchDashboard,
  };
}
