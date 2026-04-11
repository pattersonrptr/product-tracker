/**
 * Dashboard service.
 *
 * Fetches the aggregated dashboard summary from the backend
 * `GET /dashboard/summary` endpoint.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { logger } from '@/lib/logger'

/** Raw attributes returned by the backend (kebab-case). */
interface RawDashboardAttributes {
  'active-alerts': number
  'total-alerts': number
  'recent-opportunities': RawOpportunity[]
  'next-checks': RawNextCheck[]
}

interface RawOpportunity {
  id: string
  title: string
  url: string
  'current-price': number
  'alert-max-price': number
  'alert-search-term': string
  'alert-id': string
  'source-website-id': number
  'created-at'?: string | null
}

interface RawNextCheck {
  'alert-id': string
  'search-term': string
  'frequency-minutes': number
  'last-triggered-at': string | null
  'next-check-at': string | null
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

/**
 * Fetch the dashboard summary from the backend.
 * The userId parameter is kept for backward compatibility but is no longer
 * needed — the backend derives the user from the auth token.
 */
export async function getDashboardSummary(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _userId: number,
): Promise<DashboardSummary> {
  logger.debug('Fetching dashboard summary from backend')

  const response = await apiClient.get(ENDPOINTS.dashboard.summary)
  const attrs: RawDashboardAttributes =
    response.data?.data?.attributes ?? response.data?.attributes ?? {}

  const recentOpportunities: OpportunityProduct[] = (
    attrs['recent-opportunities'] ?? []
  ).map((o) => ({
    id: o.id,
    title: o.title,
    url: o.url,
    currentPrice: o['current-price'],
    alertMaxPrice: o['alert-max-price'],
    alertSearchTerm: o['alert-search-term'],
    alertId: o['alert-id'],
    sourceWebsiteId: o['source-website-id'],
    createdAt: o['created-at'] ?? undefined,
  }))

  const nextChecks: AlertNextCheck[] = (attrs['next-checks'] ?? []).map(
    (c) => ({
      alertId: c['alert-id'],
      searchTerm: c['search-term'],
      frequencyMinutes: c['frequency-minutes'],
      lastTriggeredAt: c['last-triggered-at'],
      nextCheckAt: c['next-check-at'],
    }),
  )

  return {
    activeAlerts: attrs['active-alerts'] ?? 0,
    totalAlerts: attrs['total-alerts'] ?? 0,
    recentOpportunities,
    nextChecks,
  }
}
