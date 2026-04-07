/**
 * Generic paginated resource hook.
 *
 * Eliminates the repetition from the old frontend where useProducts,
 * useSearchConfigs and useSourceWebsites were 90% identical.
 *
 * Usage:
 *   const { items, total, loading, error, pagination, setPagination, reload } =
 *     usePaginatedResource(getProducts)
 */

import { useCallback, useEffect, useState } from 'react'
import { logger } from '@/lib/logger'
import type { PaginatedResult, PaginationParams } from '@/types/api'

export interface PaginationState {
  page: number
  pageSize: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface UsePaginatedResourceResult<T> {
  items: T[]
  total: number
  loading: boolean
  error: string | null
  pagination: PaginationState
  setPagination: (state: PaginationState) => void
  reload: () => void
}

export function usePaginatedResource<T>(
  fetcher: (params: PaginationParams) => Promise<PaginatedResult<T>>,
  initialPageSize = 10,
): UsePaginatedResourceResult<T> {
  const [items, setItems] = useState<T[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState<PaginationState>({
    page: 0,
    pageSize: initialPageSize,
  })
  const [reloadTrigger, setReloadTrigger] = useState(0)

  const reload = useCallback(() => setReloadTrigger((n) => n + 1), [])

  useEffect(() => {
    let cancelled = false

    async function fetch() {
      setLoading(true)
      setError(null)
      try {
        const params: PaginationParams = {
          limit: pagination.pageSize,
          offset: pagination.page * pagination.pageSize,
          sort_by: pagination.sortBy,
          sort_order: pagination.sortOrder,
        }
        const result = await fetcher(params)
        if (!cancelled) {
          setItems(result.items)
          setTotal(result.total)
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : 'Failed to fetch data'
          setError(message)
          logger.error('usePaginatedResource fetch error', {}, err)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void fetch()
    return () => {
      cancelled = true
    }
  }, [fetcher, pagination, reloadTrigger])

  return { items, total, loading, error, pagination, setPagination, reload }
}
