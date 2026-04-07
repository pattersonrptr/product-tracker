/**
 * Search configuration service.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapCollection, unwrapSingle, wrapPayload } from '@/api/jsonapi'
import { logger } from '@/lib/logger'
import type { PaginationParams, PaginatedResult } from '@/types/api'
import type {
  SearchConfig,
  SearchConfigCreatePayload,
  SearchConfigUpdatePayload,
} from '@/types/searchConfig'

interface RawSearchConfigAttributes {
  search_term: string
  frequency_days: number
  preferred_time: string
  is_active: boolean
  user_id: number
  source_website_ids: number[]
  created_at?: string
  updated_at?: string
}

function toSearchConfig(
  raw: RawSearchConfigAttributes & { id: string },
): SearchConfig {
  return {
    id: raw.id,
    searchTerm: raw.search_term,
    frequencyDays: raw.frequency_days,
    preferredTime: raw.preferred_time,
    isActive: raw.is_active,
    userId: raw.user_id,
    sourceWebsiteIds: raw.source_website_ids ?? [],
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  }
}

function toApiPayload(
  p: SearchConfigCreatePayload | SearchConfigUpdatePayload,
): Record<string, unknown> {
  return {
    search_term: p.searchTerm,
    frequency_days: p.frequencyDays,
    preferred_time: p.preferredTime,
    is_active: p.isActive,
    user_id: p.userId,
    source_website_ids: p.sourceWebsiteIds,
  }
}

export async function getSearchConfigs(
  params: PaginationParams,
): Promise<PaginatedResult<SearchConfig>> {
  logger.debug('Fetching search configs', { params })
  const response = await apiClient.get(ENDPOINTS.searchConfigs.list, { params })
  const result = unwrapCollection<RawSearchConfigAttributes>(response.data)
  return {
    items: result.items.map(toSearchConfig),
    total: result.total,
  }
}

export async function getSearchConfigById(id: string): Promise<SearchConfig> {
  const response = await apiClient.get(ENDPOINTS.searchConfigs.byId(id))
  const raw = unwrapSingle<RawSearchConfigAttributes>(response.data)
  return toSearchConfig(raw)
}

export async function createSearchConfig(
  payload: SearchConfigCreatePayload,
): Promise<SearchConfig> {
  logger.info('Creating search config', { searchTerm: payload.searchTerm })
  const body = wrapPayload('search-configs', toApiPayload(payload))
  const response = await apiClient.post(ENDPOINTS.searchConfigs.list, body)
  const raw = unwrapSingle<RawSearchConfigAttributes>(response.data)
  return toSearchConfig(raw)
}

export async function updateSearchConfig(
  id: string,
  payload: SearchConfigUpdatePayload,
): Promise<SearchConfig> {
  logger.info('Updating search config', { id })
  const body = wrapPayload('search-configs', toApiPayload(payload), id)
  const response = await apiClient.patch(
    ENDPOINTS.searchConfigs.byId(id),
    body,
  )
  const raw = unwrapSingle<RawSearchConfigAttributes>(response.data)
  return toSearchConfig(raw)
}

export async function deleteSearchConfig(id: string): Promise<void> {
  logger.warn('Deleting search config', { id })
  await apiClient.delete(ENDPOINTS.searchConfigs.byId(id))
}
