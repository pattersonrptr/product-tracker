/**
 * Plan service.
 * Fetches available plans from the API.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapCollection, unwrapSingle } from '@/api/jsonapi'
import { logger } from '@/lib/logger'
import type { Plan } from '@/types/plan'

interface RawPlanAttributes {
  name: string
  display_name: string
  price_cents: number
  max_active_alerts: number | null
  min_frequency_minutes: number
  price_history_days: number | null
  max_sources: number | null
  has_push_notifications: boolean
  has_whatsapp_notifications: boolean
  has_api_access: boolean
  is_active: boolean
}

function toPlan(raw: RawPlanAttributes & { id: string }): Plan {
  return {
    id: raw.id,
    name: raw.name,
    displayName: raw.display_name,
    priceCents: raw.price_cents,
    maxActiveAlerts: raw.max_active_alerts,
    minFrequencyMinutes: raw.min_frequency_minutes,
    priceHistoryDays: raw.price_history_days,
    maxSources: raw.max_sources,
    hasPushNotifications: raw.has_push_notifications,
    hasWhatsappNotifications: raw.has_whatsapp_notifications,
    hasApiAccess: raw.has_api_access,
    isActive: raw.is_active,
  }
}

export async function getPlans(): Promise<Plan[]> {
  logger.debug('Fetching plans')
  const response = await apiClient.get(ENDPOINTS.plans.list)
  const result = unwrapCollection<RawPlanAttributes>(response.data)
  return result.items.map(toPlan)
}

export async function getPlanById(id: string): Promise<Plan> {
  logger.debug('Fetching plan', { id })
  const response = await apiClient.get(ENDPOINTS.plans.byId(id))
  const raw = unwrapSingle<RawPlanAttributes>(response.data)
  return toPlan(raw)
}
