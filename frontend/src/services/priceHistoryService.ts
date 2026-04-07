/**
 * Price history service.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapCollection, unwrapSingle, wrapPayload } from '@/api/jsonapi'
import { formatChartDateLabel, formatDateTime } from '@/lib/formatters'
import { logger } from '@/lib/logger'
import type { PaginatedResult } from '@/types/api'
import type {
  PriceHistory,
  PriceHistoryChartPoint,
  PriceHistoryCreatePayload,
} from '@/types/priceHistory'

interface RawPriceHistoryAttributes {
  product_id: number
  price: number
  created_at: string
}

function toPriceHistory(
  raw: RawPriceHistoryAttributes & { id: string },
): PriceHistory {
  return {
    id: raw.id,
    productId: raw.product_id,
    price: raw.price,
    createdAt: raw.created_at,
  }
}

export async function getPriceHistoryByProduct(
  productId: string,
): Promise<PriceHistory[]> {
  logger.debug('Fetching price history', { productId })
  const response = await apiClient.get(
    ENDPOINTS.priceHistory.byProduct(productId),
  )
  const result = unwrapCollection<RawPriceHistoryAttributes>(response.data)
  return result.items
    .map(toPriceHistory)
    .sort(
      (a, b) =>
        new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
    )
}

export async function getLatestPriceByProduct(
  productId: string,
): Promise<PriceHistory | null> {
  try {
    const response = await apiClient.get(
      ENDPOINTS.priceHistory.latestByProduct(productId),
    )
    const raw = unwrapSingle<RawPriceHistoryAttributes>(response.data)
    return toPriceHistory(raw)
  } catch {
    return null
  }
}

export async function createPriceHistory(
  payload: PriceHistoryCreatePayload,
): Promise<PriceHistory> {
  logger.info('Creating price history entry', { productId: payload.productId })
  const body = wrapPayload('price-histories', {
    product_id: payload.productId,
    price: payload.price,
  })
  const response = await apiClient.post(ENDPOINTS.priceHistory.list, body)
  const raw = unwrapSingle<RawPriceHistoryAttributes>(response.data)
  return toPriceHistory(raw)
}

/** Returns price history formatted for use in Recharts */
export async function getPriceHistoryChartData(
  productId: string,
): Promise<PriceHistoryChartPoint[]> {
  const history = await getPriceHistoryByProduct(productId)
  return history.map((entry) => ({
    price: entry.price,
    dateLabel: formatChartDateLabel(entry.createdAt),
    dateTime: formatDateTime(entry.createdAt),
  }))
}

export async function listPriceHistories(params: {
  limit: number
  offset: number
}): Promise<PaginatedResult<PriceHistory>> {
  const response = await apiClient.get(ENDPOINTS.priceHistory.list, { params })
  const result = unwrapCollection<RawPriceHistoryAttributes>(response.data)
  return {
    items: result.items.map(toPriceHistory),
    total: result.total,
  }
}

export async function deletePriceHistory(id: string): Promise<void> {
  logger.warn('Deleting price history entry', { id })
  await apiClient.delete(ENDPOINTS.priceHistory.byId(id))
}
