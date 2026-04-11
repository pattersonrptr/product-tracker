/**
 * Tests for services/dashboardService.ts
 *
 * We mock the apiClient and verify that getDashboardSummary correctly
 * aggregates alerts and products into the summary shape used by the
 * dashboard page.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { getDashboardSummary } from '@/services/dashboardService'

// ---------- mocks ----------

const { mockGet, mockGetExecutionStatus } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockGetExecutionStatus: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet },
}))

vi.mock('@/services/searchConfigService', () => ({
  getExecutionStatus: mockGetExecutionStatus,
}))

vi.mock('@/lib/logger', () => ({
  logger: { debug: vi.fn(), warn: vi.fn(), error: vi.fn() },
}))

// ---------- helpers ----------

function alertsCollectionResponse(
  items: { id: string; attrs: Record<string, unknown> }[],
) {
  return {
    data: {
      data: items.map((i) => ({
        id: i.id,
        type: 'price-alerts',
        attributes: i.attrs,
      })),
      meta: { total: items.length },
    },
  }
}

function productsCollectionResponse(
  items: { id: string; attrs: Record<string, unknown> }[],
) {
  return {
    data: {
      data: items.map((i) => ({
        id: i.id,
        type: 'products',
        attributes: i.attrs,
      })),
      meta: { total: items.length },
    },
  }
}

const ALERT_1 = {
  search_term: 'iPhone 15',
  max_price: 5000,
  is_active: true,
  frequency_minutes: 60,
  last_triggered_at: '2025-01-15T10:00:00Z',
  user_id: 1,
  search_config_id: 10,
  source_website_ids: [1],
  created_at: '2025-01-10T08:00:00Z',
  updated_at: '2025-01-15T10:00:00Z',
}

const ALERT_2_INACTIVE = {
  search_term: 'Galaxy S24',
  max_price: 3000,
  is_active: false,
  frequency_minutes: 120,
  last_triggered_at: null,
  user_id: 1,
  search_config_id: null,
  source_website_ids: [2],
  created_at: '2025-01-12T09:00:00Z',
  updated_at: '2025-01-12T09:00:00Z',
}

const PRODUCT_MATCH = {
  title: 'iPhone 15 128GB',
  url: 'https://example.com/iphone',
  current_price: 4200,
  source_website_id: 1,
  is_available: true,
  condition: 'new',
  created_at: '2025-01-14T12:00:00Z',
  updated_at: '2025-01-14T12:00:00Z',
}

const PRODUCT_EXPENSIVE = {
  title: 'iPhone 15 Pro Max 512GB',
  url: 'https://example.com/iphone-pro',
  current_price: 8000,
  source_website_id: 1,
  is_available: true,
  condition: 'new',
  created_at: '2025-01-13T12:00:00Z',
  updated_at: '2025-01-13T12:00:00Z',
}

beforeEach(() => {
  vi.resetAllMocks()
  // Default: execution status returns a successful run matching ALERT_1's last_triggered_at
  mockGetExecutionStatus.mockResolvedValue({
    searchConfigId: 10,
    status: 'success',
    startedAt: '2025-01-15T10:00:00Z',
    finishedAt: '2025-01-15T10:05:00Z',
    resultsCount: 5,
    errorMessage: null,
  })
})

describe('getDashboardSummary', () => {
  it('returns correct alert counts (active vs total)', async () => {
    mockGet
      // First call: user's alerts
      .mockResolvedValueOnce(
        alertsCollectionResponse([
          { id: '1', attrs: ALERT_1 },
          { id: '2', attrs: ALERT_2_INACTIVE },
        ]),
      )
      // Second call: products for active alert #1
      .mockResolvedValueOnce(productsCollectionResponse([]))

    const summary = await getDashboardSummary(1)

    expect(summary.activeAlerts).toBe(1)
    expect(summary.totalAlerts).toBe(2)
  })

  it('only fetches products for active alerts', async () => {
    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([
          { id: '1', attrs: ALERT_1 },
          { id: '2', attrs: ALERT_2_INACTIVE },
        ]),
      )
      .mockResolvedValueOnce(productsCollectionResponse([]))

    await getDashboardSummary(1)

    // 1 call for alerts + 1 call for products of the single active alert
    expect(mockGet).toHaveBeenCalledTimes(2)
  })

  it('identifies opportunity products (price <= maxPrice)', async () => {
    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([{ id: '1', attrs: ALERT_1 }]),
      )
      .mockResolvedValueOnce(
        productsCollectionResponse([
          { id: 'p1', attrs: PRODUCT_MATCH },
          { id: 'p2', attrs: PRODUCT_EXPENSIVE },
        ]),
      )

    const summary = await getDashboardSummary(1)

    // Only PRODUCT_MATCH (4200) is <= maxPrice (5000)
    expect(summary.recentOpportunities).toHaveLength(1)
    expect(summary.recentOpportunities[0].id).toBe('p1')
    expect(summary.recentOpportunities[0].currentPrice).toBe(4200)
    expect(summary.recentOpportunities[0].alertMaxPrice).toBe(5000)
    expect(summary.recentOpportunities[0].alertSearchTerm).toBe('iPhone 15')
    expect(summary.recentOpportunities[0].alertId).toBe('1')
  })

  it('computes nextChecks for active alerts', async () => {
    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([{ id: '1', attrs: ALERT_1 }]),
      )
      .mockResolvedValueOnce(productsCollectionResponse([]))

    // Mock execution status for search_config_id=10
    mockGetExecutionStatus.mockResolvedValueOnce({
      searchConfigId: 10,
      status: 'success',
      startedAt: '2025-01-15T10:00:00Z',
      finishedAt: '2025-01-15T10:05:00Z',
      resultsCount: 5,
      errorMessage: null,
    })

    const summary = await getDashboardSummary(1)

    expect(summary.nextChecks).toHaveLength(1)
    expect(summary.nextChecks[0].alertId).toBe('1')
    expect(summary.nextChecks[0].searchTerm).toBe('iPhone 15')
    expect(summary.nextChecks[0].frequencyMinutes).toBe(60)

    // startedAt is 2025-01-15T10:00:00Z, frequency is 60min
    // so nextCheckAt should be 2025-01-15T11:00:00Z
    const nextCheck = new Date(summary.nextChecks[0].nextCheckAt!)
    expect(nextCheck.getUTCHours()).toBe(11)
    expect(nextCheck.getUTCMinutes()).toBe(0)
  })

  it('sets nextCheckAt to null when execution has no startedAt', async () => {
    const alertNoTrigger = { ...ALERT_1, last_triggered_at: null, is_active: true }

    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([{ id: '3', attrs: alertNoTrigger }]),
      )
      .mockResolvedValueOnce(productsCollectionResponse([]))

    // Override: execution status has no startedAt
    mockGetExecutionStatus.mockResolvedValueOnce({
      searchConfigId: 10,
      status: 'idle',
      startedAt: null,
      finishedAt: null,
      resultsCount: null,
      errorMessage: null,
    })

    const summary = await getDashboardSummary(1)

    expect(summary.nextChecks[0].nextCheckAt).toBeNull()
    expect(summary.nextChecks[0].lastTriggeredAt).toBeNull()
  })

  it('returns empty summary when user has no alerts', async () => {
    mockGet.mockResolvedValueOnce(alertsCollectionResponse([]))

    const summary = await getDashboardSummary(1)

    expect(summary.activeAlerts).toBe(0)
    expect(summary.totalAlerts).toBe(0)
    expect(summary.recentOpportunities).toEqual([])
    expect(summary.nextChecks).toEqual([])
    // Only 1 call (alerts fetch), no product fetches
    expect(mockGet).toHaveBeenCalledTimes(1)
  })

  it('gracefully handles product fetch errors for individual alerts', async () => {
    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([{ id: '1', attrs: ALERT_1 }]),
      )
      // Products endpoint fails
      .mockRejectedValueOnce(new Error('Timeout'))

    const summary = await getDashboardSummary(1)

    // Should still return a valid summary, just no opportunities
    expect(summary.activeAlerts).toBe(1)
    expect(summary.recentOpportunities).toEqual([])
    expect(summary.nextChecks).toHaveLength(1)
  })

  it('limits opportunities to 20 items', async () => {
    // Create many matching products
    const manyProducts = Array.from({ length: 25 }, (_, i) => ({
      id: `p${i}`,
      attrs: {
        ...PRODUCT_MATCH,
        title: `Product ${i}`,
        created_at: new Date(2025, 0, 15, 12, i).toISOString(),
      },
    }))

    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([{ id: '1', attrs: ALERT_1 }]),
      )
      .mockResolvedValueOnce(productsCollectionResponse(manyProducts))

    const summary = await getDashboardSummary(1)

    expect(summary.recentOpportunities.length).toBeLessThanOrEqual(20)
  })

  it('sorts opportunities by most recent first', async () => {
    const olderProduct = {
      ...PRODUCT_MATCH,
      title: 'Older product',
      current_price: 4000,
      created_at: '2025-01-10T12:00:00Z',
    }
    const newerProduct = {
      ...PRODUCT_MATCH,
      title: 'Newer product',
      current_price: 4500,
      created_at: '2025-01-15T12:00:00Z',
    }

    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([{ id: '1', attrs: ALERT_1 }]),
      )
      .mockResolvedValueOnce(
        productsCollectionResponse([
          { id: 'p-old', attrs: olderProduct },
          { id: 'p-new', attrs: newerProduct },
        ]),
      )

    const summary = await getDashboardSummary(1)

    expect(summary.recentOpportunities[0].title).toBe('Newer product')
    expect(summary.recentOpportunities[1].title).toBe('Older product')
  })

  it('sorts nextChecks by nearest check first', async () => {
    const alert1 = {
      ...ALERT_1,
      frequency_minutes: 30,
      last_triggered_at: '2025-01-15T10:00:00Z',
      search_config_id: 10,
    }
    const alert2 = {
      ...ALERT_1,
      search_term: 'Pixel 9',
      frequency_minutes: 120,
      last_triggered_at: '2025-01-15T08:00:00Z',
      search_config_id: 20,
    }

    mockGet
      .mockResolvedValueOnce(
        alertsCollectionResponse([
          { id: '1', attrs: alert1 },
          { id: '2', attrs: alert2 },
        ]),
      )
      // Products for alert1
      .mockResolvedValueOnce(productsCollectionResponse([]))
      // Products for alert2
      .mockResolvedValueOnce(productsCollectionResponse([]))

    // Mock execution status for each search config
    mockGetExecutionStatus
      .mockResolvedValueOnce({
        searchConfigId: 10,
        status: 'success',
        startedAt: '2025-01-15T10:00:00Z',
        finishedAt: null,
        resultsCount: null,
        errorMessage: null,
      })
      .mockResolvedValueOnce({
        searchConfigId: 20,
        status: 'success',
        startedAt: '2025-01-15T08:00:00Z',
        finishedAt: null,
        resultsCount: null,
        errorMessage: null,
      })

    const summary = await getDashboardSummary(1)

    // alert2 next check: 08:00 + 120min = 10:00
    // alert1 next check: 10:00 + 30min = 10:30
    // So alert2 should come first (earlier check)
    expect(summary.nextChecks[0].searchTerm).toBe('Pixel 9')
    expect(summary.nextChecks[1].searchTerm).toBe('iPhone 15')
  })
})
