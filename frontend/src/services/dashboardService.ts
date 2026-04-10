/**
 * Dashboard service.
 * Aggregates summary data from existing API endpoints.
 */

import { logger } from '@/lib/logger'
import { getPriceAlertsByUser } from '@/services/priceAlertService'
import { getProducts } from '@/services/productService'
import type { PriceAlert } from '@/types/priceAlert'
import type { Product } from '@/types/product'

export interface RecentOpportunity {
  product: Product
  alert: PriceAlert
}

export interface NextCheck {
  alertId: string
  searchTerm: string
  frequencyMinutes: number
  lastTriggeredAt?: string
  /** ISO string of the estimated next check */
  nextCheckAt: string
}

export interface DashboardSummary {
  activeAlertsCount: number
  recentOpportunities: RecentOpportunity[]
  nextChecks: NextCheck[]
}

/** Compute estimated next check time from last trigger and frequency */
function computeNextCheck(alert: PriceAlert): NextCheck {
  const freqMs = alert.frequencyMinutes * 60 * 1000
  const base = alert.lastTriggeredAt
    ? new Date(alert.lastTriggeredAt).getTime()
    : new Date(alert.createdAt ?? Date.now()).getTime()
  const nextCheckAt = new Date(base + freqMs).toISOString()
  return {
    alertId: alert.id,
    searchTerm: alert.searchTerm,
    frequencyMinutes: alert.frequencyMinutes,
    lastTriggeredAt: alert.lastTriggeredAt,
    nextCheckAt,
  }
}

export async function getDashboardSummary(userId: number): Promise<DashboardSummary> {
  logger.debug('Fetching dashboard summary', { userId })

  const alerts = await getPriceAlertsByUser(userId)
  const activeAlerts = alerts.filter((a) => a.isActive)

  // Fetch recent products (up to 50) and find opportunities
  const { items: products } = await getProducts({ limit: 50, offset: 0 })

  const recentOpportunities: RecentOpportunity[] = []
  for (const product of products) {
    if (product.currentPrice == null) continue
    for (const alert of activeAlerts) {
      if (
        product.currentPrice <= alert.maxPrice &&
        product.title.toLowerCase().includes(alert.searchTerm.toLowerCase())
      ) {
        recentOpportunities.push({ product, alert })
        break
      }
    }
    if (recentOpportunities.length >= 5) break
  }

  const nextChecks = activeAlerts
    .map(computeNextCheck)
    .sort((a, b) => a.nextCheckAt.localeCompare(b.nextCheckAt))
    .slice(0, 5)

  return {
    activeAlertsCount: activeAlerts.length,
    recentOpportunities,
    nextChecks,
  }
}
