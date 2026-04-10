/**
 * Hook to fetch and cache the dashboard summary.
 */

import { useCallback, useEffect, useState } from 'react'
import { logger } from '@/lib/logger'
import {
  getDashboardSummary,
  type DashboardSummary,
} from '@/services/dashboardService'

export interface UseDashboardSummaryResult {
  summary: DashboardSummary | null
  loading: boolean
  error: string | null
  reload: () => void
}

export function useDashboardSummary(
  userId: number | null,
): UseDashboardSummaryResult {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadTrigger, setReloadTrigger] = useState(0)

  const reload = useCallback(() => setReloadTrigger((n) => n + 1), [])

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    let cancelled = false

    async function fetch() {
      setLoading(true)
      setError(null)
      try {
        const data = await getDashboardSummary(userId!)
        if (!cancelled) {
          setSummary(data)
        }
      } catch (err) {
        if (!cancelled) {
          const msg =
            err instanceof Error ? err.message : 'Failed to load dashboard'
          setError(msg)
          logger.error('Dashboard summary fetch failed', {}, err)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetch()
    return () => {
      cancelled = true
    }
  }, [userId, reloadTrigger])

  return { summary, loading, error, reload }
}
