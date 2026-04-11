import { apiClient } from '@/api/client'

export interface AdminSummary {
  totalUsers: number
  activeUsers: number
  totalProducts: number
  totalAlerts: number
  activeAlerts: number
  totalSourceWebsites: number
  activeSourceWebsites: number
  recentExecutions: ScraperExecution[]
  scraperStats: {
    recentTotal: number
    successCount: number
    failedCount: number
  }
}

export interface ScraperExecution {
  id: number
  searchConfigId: number
  status: string
  resultsCount: number | null
  errorMessage: string | null
  startedAt: string | null
  finishedAt: string | null
}

export async function getAdminSummary(): Promise<AdminSummary> {
  const res = await apiClient.get('/admin/summary')
  const attrs = res.data.data.attributes

  return {
    totalUsers: attrs['total-users'],
    activeUsers: attrs['active-users'],
    totalProducts: attrs['total-products'],
    totalAlerts: attrs['total-alerts'],
    activeAlerts: attrs['active-alerts'],
    totalSourceWebsites: attrs['total-source-websites'],
    activeSourceWebsites: attrs['active-source-websites'],
    recentExecutions: (attrs['recent-executions'] ?? []).map(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e: any) => ({
        id: e.id,
        searchConfigId: e['search-config-id'],
        status: e.status,
        resultsCount: e['results-count'],
        errorMessage: e['error-message'],
        startedAt: e['started-at'],
        finishedAt: e['finished-at'],
      }),
    ),
    scraperStats: {
      recentTotal: attrs['scraper-stats']['recent-total'],
      successCount: attrs['scraper-stats']['success-count'],
      failedCount: attrs['scraper-stats']['failed-count'],
    },
  }
}
