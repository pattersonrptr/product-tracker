/**
 * Hook for loading a product and its full price history.
 * Used by ProductDetailPage.
 */

import { useCallback, useEffect, useState } from 'react'
import { getProductById } from '@/services/productService'
import { getPriceHistoryChartData } from '@/services/priceHistoryService'
import { logger } from '@/lib/logger'
import type { Product } from '@/types/product'
import type { PriceHistoryChartPoint } from '@/types/priceHistory'

interface UseProductDetailsResult {
  product: Product | null
  chartData: PriceHistoryChartPoint[]
  loading: boolean
  error: string | null
  reload: () => void
}

export function useProductDetails(productId: string): UseProductDetailsResult {
  const [product, setProduct] = useState<Product | null>(null)
  const [chartData, setChartData] = useState<PriceHistoryChartPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [trigger, setTrigger] = useState(0)

  const reload = useCallback(() => setTrigger((n) => n + 1), [])

  useEffect(() => {
    if (!productId) return
    let cancelled = false

    async function fetch() {
      setLoading(true)
      setError(null)
      try {
        const [p, chart] = await Promise.all([
          getProductById(productId),
          getPriceHistoryChartData(productId),
        ])
        if (!cancelled) {
          setProduct(p)
          setChartData(chart)
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : 'Failed to load product details'
          setError(message)
          logger.error('useProductDetails fetch error', { productId }, err)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void fetch()
    return () => {
      cancelled = true
    }
  }, [productId, trigger])

  return { product, chartData, loading, error, reload }
}
