/**
 * Hook to fetch and cache the dashboard summary for the current user.
 */

import { useCallback, useEffect, useState } from 'react'
import { logger } from '@/lib/logger'
import { getDashboardSummary } from '@/services/dashboardService'
import type { DashboardSummary } from '@/services/dashboardService'

export interface UseDashboardSummaryResult {
  summary: DashboardSummary | null
  loading: boolean
  error: string | null
  reload: () => void
}

export function useDashboardSummary(userId: number | null): UseDashboardSummaryResult {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadTrigger, setReloadTrigger] = useState(0)

  const reload = useCallback(() => setReloadTrigger((n) => n + 1), [])

  useEffect(() => {
    if (userId === null) {
      setLoading(false)
      return
    }

    const currentUserId = userId
    let cancelled = false

    async function fetch() {
      setLoading(true)
      setError(null)
      try {
        const data = await getDashboardSummary(currentUserId)
        if (!cancelled) setSummary(data)
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Failed to load dashboard'
          setError(message)
          logger.error('useDashboardSummary fetch error', {}, err)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void fetch()
    return () => {
      cancelled = true
    }
  }, [userId, reloadTrigger])

  return { summary, loading, error, reload }
}
