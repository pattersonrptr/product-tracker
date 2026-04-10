/**
 * Dashboard service.
 *
 * Aggregates data from multiple endpoints to build the dashboard summary.
 * No dedicated backend endpoint yet — we fetch price alerts for the current
 * user and assemble the summary client-side.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapCollection } from '@/api/jsonapi'
import { logger } from '@/lib/logger'
import type { PriceAlert } from '@/types/priceAlert'

/** Raw attributes from the price-alerts API (snake_case) */
interface RawPriceAlertAttributes {
  search_term: string
  max_price: number
  is_active: boolean
  frequency_minutes: number
  last_triggered_at?: string | null
  user_id?: number | null
  search_config_id?: number | null
  source_website_ids: number[]
  created_at?: string
  updated_at?: string
}

/** Raw product attributes from the products sub-endpoint */
interface RawProductAttributes {
  url: string
  title: string
  current_price?: number
  source_website_id: number
  is_available: boolean
  condition: string
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

export interface OpportunityProduct {
  id: string
  title: string
  url: string
  currentPrice: number
  alertMaxPrice: number
  alertSearchTerm: string
  alertId: string
  sourceWebsiteId: number
  createdAt?: string
}

export interface AlertNextCheck {
  alertId: string
  searchTerm: string
  frequencyMinutes: number
  lastTriggeredAt: string | null
  nextCheckAt: string | null
}

export interface DashboardSummary {
  activeAlerts: number
  totalAlerts: number
  recentOpportunities: OpportunityProduct[]
  nextChecks: AlertNextCheck[]
}

function computeNextCheck(
  lastTriggered: string | null | undefined,
  frequencyMinutes: number,
): string | null {
  if (!lastTriggered) return null
  const next = new Date(lastTriggered)
  next.setMinutes(next.getMinutes() + frequencyMinutes)
  return next.toISOString()
}

/**
 * Build a dashboard summary for the given user.
 *
 * 1. Fetch all price alerts for the user
 * 2. For each active alert, fetch matching products (limited to 5 per alert)
 * 3. Compute next check times
 */
export async function getDashboardSummary(
  userId: number,
): Promise<DashboardSummary> {
  logger.debug('Building dashboard summary', { userId })

  // 1. Fetch user's alerts
  const alertsResponse = await apiClient.get(
    ENDPOINTS.priceAlerts.byUser(userId),
  )
  const alertsResult = unwrapCollection<RawPriceAlertAttributes>(
    alertsResponse.data,
  )

  const alerts: PriceAlert[] = alertsResult.items.map((raw) => ({
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
  }))

  const activeAlerts = alerts.filter((a) => a.isActive)

  // 2. Fetch matching products for active alerts (limited scope)
  const opportunities: OpportunityProduct[] = []

  const productFetches = activeAlerts.slice(0, 10).map(async (alert) => {
    try {
      const resp = await apiClient.get(
        ENDPOINTS.priceAlerts.products(alert.id),
        { params: { limit: 5, offset: 0 } },
      )
      const productsResult = unwrapCollection<RawProductAttributes>(resp.data)
      for (const p of productsResult.items) {
        const price = p.current_price
        if (price !== undefined && price <= alert.maxPrice) {
          opportunities.push({
            id: p.id,
            title: p.title,
            url: p.url,
            currentPrice: price,
            alertMaxPrice: alert.maxPrice,
            alertSearchTerm: alert.searchTerm,
            alertId: alert.id,
            sourceWebsiteId: p.source_website_id,
            createdAt: p.created_at,
          })
        }
      }
    } catch (err) {
      logger.warn('Failed to fetch products for alert', { alertId: alert.id }, err)
    }
  })

  await Promise.all(productFetches)

  // Sort by most recent first
  opportunities.sort(
    (a, b) =>
      new Date(b.createdAt ?? 0).getTime() -
      new Date(a.createdAt ?? 0).getTime(),
  )

  // 3. Compute next checks
  const nextChecks: AlertNextCheck[] = activeAlerts.map((alert) => ({
    alertId: alert.id,
    searchTerm: alert.searchTerm,
    frequencyMinutes: alert.frequencyMinutes,
    lastTriggeredAt: alert.lastTriggeredAt ?? null,
    nextCheckAt: computeNextCheck(
      alert.lastTriggeredAt,
      alert.frequencyMinutes,
    ),
  }))

  // Sort by nearest check first
  nextChecks.sort((a, b) => {
    if (!a.nextCheckAt) return 1
    if (!b.nextCheckAt) return -1
    return (
      new Date(a.nextCheckAt).getTime() - new Date(b.nextCheckAt).getTime()
    )
  })

  return {
    activeAlerts: activeAlerts.length,
    totalAlerts: alerts.length,
    recentOpportunities: opportunities.slice(0, 20),
    nextChecks,
  }
}
