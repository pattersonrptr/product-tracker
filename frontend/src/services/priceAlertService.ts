/**
 * Price alert service.
 * CRUD operations for /price-alerts.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapCollection, unwrapSingle, wrapPayload } from '@/api/jsonapi'
import { logger } from '@/lib/logger'
import type { PaginationParams, PaginatedResult } from '@/types/api'
import type {
  PriceAlert,
  PriceAlertCreatePayload,
  PriceAlertUpdatePayload,
} from '@/types/priceAlert'

/** Raw attributes from the API (snake_case) */
interface RawPriceAlertAttributes {
  search_term: string
  max_price: number
  is_active: boolean
  frequency_minutes: number
  last_triggered_at?: string
  user_id: number
  search_config_id?: number
  source_website_ids: number[]
  created_at?: string
  updated_at?: string
}

function toPriceAlert(raw: RawPriceAlertAttributes & { id: string }): PriceAlert {
  return {
    id: raw.id,
    searchTerm: raw.search_term,
    maxPrice: raw.max_price,
    isActive: raw.is_active,
    frequencyMinutes: raw.frequency_minutes,
    lastTriggeredAt: raw.last_triggered_at,
    userId: raw.user_id,
    searchConfigId: raw.search_config_id,
    sourceWebsiteIds: raw.source_website_ids ?? [],
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  }
}

function toApiPayload(
  payload: PriceAlertCreatePayload | PriceAlertUpdatePayload,
): Record<string, unknown> {
  return {
    search_term: payload.searchTerm,
    max_price: payload.maxPrice,
    is_active: payload.isActive,
    frequency_minutes: payload.frequencyMinutes,
    user_id: payload.userId,
    source_website_ids: payload.sourceWebsiteIds,
  }
}

export async function getPriceAlerts(
  params: PaginationParams,
): Promise<PaginatedResult<PriceAlert>> {
  logger.debug('Fetching price alerts', { params })
  const response = await apiClient.get(ENDPOINTS.priceAlerts.list, { params })
  const result = unwrapCollection<RawPriceAlertAttributes>(response.data)
  return {
    items: result.items.map(toPriceAlert),
    total: result.total,
  }
}

export async function getPriceAlertsByUser(
  userId: number,
): Promise<PriceAlert[]> {
  logger.debug('Fetching price alerts for user', { userId })
  const response = await apiClient.get(ENDPOINTS.priceAlerts.byUser(userId))
  const result = unwrapCollection<RawPriceAlertAttributes>(response.data)
  return result.items.map(toPriceAlert)
}

export async function getPriceAlertById(id: string): Promise<PriceAlert> {
  logger.debug('Fetching price alert by id', { id })
  const response = await apiClient.get(ENDPOINTS.priceAlerts.byId(id))
  const raw = unwrapSingle<RawPriceAlertAttributes>(response.data)
  return toPriceAlert(raw)
}

export async function createPriceAlert(
  payload: PriceAlertCreatePayload,
): Promise<PriceAlert> {
  logger.info('Creating price alert', { searchTerm: payload.searchTerm })
  const body = wrapPayload('price-alerts', toApiPayload(payload))
  const response = await apiClient.post(ENDPOINTS.priceAlerts.list, body)
  const raw = unwrapSingle<RawPriceAlertAttributes>(response.data)
  return toPriceAlert(raw)
}

export async function updatePriceAlert(
  id: string,
  payload: PriceAlertUpdatePayload,
): Promise<PriceAlert> {
  logger.info('Updating price alert', { id })
  const body = wrapPayload('price-alerts', toApiPayload(payload), id)
  const response = await apiClient.put(ENDPOINTS.priceAlerts.byId(id), body)
  const raw = unwrapSingle<RawPriceAlertAttributes>(response.data)
  return toPriceAlert(raw)
}

export async function deletePriceAlert(id: string): Promise<void> {
  logger.warn('Deleting price alert', { id })
  await apiClient.delete(ENDPOINTS.priceAlerts.byId(id))
}
