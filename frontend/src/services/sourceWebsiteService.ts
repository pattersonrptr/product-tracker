/**
 * Source website service.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapCollection, unwrapSingle, wrapPayload } from '@/api/jsonapi'
import { logger } from '@/lib/logger'
import type { PaginationParams, PaginatedResult } from '@/types/api'
import type {
  SourceWebsite,
  SourceWebsiteCreatePayload,
  SourceWebsiteUpdatePayload,
} from '@/types/sourceWebsite'

interface RawSourceWebsiteAttributes {
  name: string
  base_url: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

function toSourceWebsite(
  raw: RawSourceWebsiteAttributes & { id: string },
): SourceWebsite {
  return {
    id: raw.id,
    name: raw.name,
    baseUrl: raw.base_url,
    isActive: raw.is_active,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  }
}

function toApiPayload(
  p: SourceWebsiteCreatePayload | SourceWebsiteUpdatePayload,
): Record<string, unknown> {
  return {
    name: p.name,
    base_url: p.baseUrl,
    is_active: p.isActive,
  }
}

export async function getSourceWebsites(
  params: PaginationParams,
): Promise<PaginatedResult<SourceWebsite>> {
  logger.debug('Fetching source websites', { params })
  const response = await apiClient.get(ENDPOINTS.sourceWebsites.list, {
    params,
  })
  const result = unwrapCollection<RawSourceWebsiteAttributes>(response.data)
  return {
    items: result.items.map(toSourceWebsite),
    total: result.total,
  }
}

export async function getAllSourceWebsites(): Promise<SourceWebsite[]> {
  const response = await apiClient.get(ENDPOINTS.sourceWebsites.list, {
    params: { limit: 100, offset: 0 },
  })
  const result = unwrapCollection<RawSourceWebsiteAttributes>(response.data)
  return result.items.map(toSourceWebsite)
}

export async function getSourceWebsiteById(
  id: string,
): Promise<SourceWebsite> {
  const response = await apiClient.get(ENDPOINTS.sourceWebsites.byId(id))
  const raw = unwrapSingle<RawSourceWebsiteAttributes>(response.data)
  return toSourceWebsite(raw)
}

export async function createSourceWebsite(
  payload: SourceWebsiteCreatePayload,
): Promise<SourceWebsite> {
  logger.info('Creating source website', { name: payload.name })
  const body = wrapPayload('source-websites', toApiPayload(payload))
  const response = await apiClient.post(ENDPOINTS.sourceWebsites.list, body)
  const raw = unwrapSingle<RawSourceWebsiteAttributes>(response.data)
  return toSourceWebsite(raw)
}

export async function updateSourceWebsite(
  id: string,
  payload: SourceWebsiteUpdatePayload,
): Promise<SourceWebsite> {
  logger.info('Updating source website', { id })
  const body = wrapPayload('source-websites', toApiPayload(payload), id)
  const response = await apiClient.patch(
    ENDPOINTS.sourceWebsites.byId(id),
    body,
  )
  const raw = unwrapSingle<RawSourceWebsiteAttributes>(response.data)
  return toSourceWebsite(raw)
}

export async function deleteSourceWebsite(id: string): Promise<void> {
  logger.warn('Deleting source website', { id })
  await apiClient.delete(ENDPOINTS.sourceWebsites.byId(id))
}
