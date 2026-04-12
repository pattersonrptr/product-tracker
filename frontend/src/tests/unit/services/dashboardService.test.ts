/**
 * Tests for services/dashboardService.ts
 *
 * The service now fetches the aggregated summary from a single
 * `GET /dashboard/summary` backend endpoint and maps the kebab-case
 * JSON:API attributes to camelCase.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { getDashboardSummary } from '@/services/dashboardService'

// ---------- mocks ----------

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet },
}))

vi.mock('@/lib/logger', () => ({
  logger: { debug: vi.fn(), warn: vi.fn(), error: vi.fn() },
}))

// ---------- helpers ----------

function summaryResponse(attrs: Record<string, unknown>) {
  return {
    data: {
      data: {
        type: 'dashboard-summary',
        attributes: attrs,
      },
    },
  }
}

const OPPORTUNITY_1 = {
  id: 'p1',
  title: 'iPhone 15 128GB',
  url: 'https://example.com/iphone',
  'current-price': 4200,
  'alert-max-price': 5000,
  'alert-search-term': 'iPhone 15',
  'alert-id': '1',
  'source-website-id': 1,
  'created-at': '2025-01-14T12:00:00Z',
}

const OPPORTUNITY_2 = {
  id: 'p2',
  title: 'Galaxy S24 Ultra',
  url: 'https://example.com/galaxy',
  'current-price': 2800,
  'alert-max-price': 3000,
  'alert-search-term': 'Galaxy S24',
  'alert-id': '2',
  'source-website-id': 2,
  'created-at': '2025-01-15T12:00:00Z',
}

const NEXT_CHECK_1 = {
  'alert-id': '1',
  'search-term': 'iPhone 15',
  'frequency-minutes': 60,
  'last-triggered-at': '2025-01-15T10:00:00Z',
  'next-check-at': '2025-01-15T11:00:00Z',
}

const NEXT_CHECK_2 = {
  'alert-id': '2',
  'search-term': 'Galaxy S24',
  'frequency-minutes': 120,
  'last-triggered-at': null,
  'next-check-at': null,
}

beforeEach(() => {
  vi.resetAllMocks()
})

describe('getDashboardSummary', () => {
  it('returns correct alert counts (active vs total)', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 3,
        'total-alerts': 5,
        'recent-opportunities': [],
        'next-checks': [],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.activeAlerts).toBe(3)
    expect(summary.totalAlerts).toBe(5)
  })

  it('makes a single API call to the summary endpoint', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 1,
        'total-alerts': 2,
        'recent-opportunities': [],
        'next-checks': [],
      }),
    )

    await getDashboardSummary(1)

    expect(mockGet).toHaveBeenCalledTimes(1)
  })

  it('maps opportunity attributes from kebab-case to camelCase', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 1,
        'total-alerts': 1,
        'recent-opportunities': [OPPORTUNITY_1],
        'next-checks': [],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.recentOpportunities).toHaveLength(1)
    expect(summary.recentOpportunities[0].id).toBe('p1')
    expect(summary.recentOpportunities[0].currentPrice).toBe(4200)
    expect(summary.recentOpportunities[0].alertMaxPrice).toBe(5000)
    expect(summary.recentOpportunities[0].alertSearchTerm).toBe('iPhone 15')
    expect(summary.recentOpportunities[0].alertId).toBe('1')
    expect(summary.recentOpportunities[0].sourceWebsiteId).toBe(1)
    expect(summary.recentOpportunities[0].createdAt).toBe('2025-01-14T12:00:00Z')
  })

  it('maps nextCheck attributes from kebab-case to camelCase', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 1,
        'total-alerts': 1,
        'recent-opportunities': [],
        'next-checks': [NEXT_CHECK_1],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.nextChecks).toHaveLength(1)
    expect(summary.nextChecks[0].alertId).toBe('1')
    expect(summary.nextChecks[0].searchTerm).toBe('iPhone 15')
    expect(summary.nextChecks[0].frequencyMinutes).toBe(60)
    expect(summary.nextChecks[0].lastTriggeredAt).toBe('2025-01-15T10:00:00Z')
    expect(summary.nextChecks[0].nextCheckAt).toBe('2025-01-15T11:00:00Z')
  })

  it('handles null nextCheckAt and lastTriggeredAt', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 1,
        'total-alerts': 1,
        'recent-opportunities': [],
        'next-checks': [NEXT_CHECK_2],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.nextChecks[0].nextCheckAt).toBeNull()
    expect(summary.nextChecks[0].lastTriggeredAt).toBeNull()
  })

  it('returns empty summary when user has no alerts', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 0,
        'total-alerts': 0,
        'recent-opportunities': [],
        'next-checks': [],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.activeAlerts).toBe(0)
    expect(summary.totalAlerts).toBe(0)
    expect(summary.recentOpportunities).toEqual([])
    expect(summary.nextChecks).toEqual([])
    expect(mockGet).toHaveBeenCalledTimes(1)
  })

  it('returns multiple opportunities and nextChecks', async () => {
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 2,
        'total-alerts': 3,
        'recent-opportunities': [OPPORTUNITY_1, OPPORTUNITY_2],
        'next-checks': [NEXT_CHECK_1, NEXT_CHECK_2],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.recentOpportunities).toHaveLength(2)
    expect(summary.nextChecks).toHaveLength(2)
    expect(summary.recentOpportunities[0].id).toBe('p1')
    expect(summary.recentOpportunities[1].id).toBe('p2')
  })

  it('defaults to empty values when attributes are missing', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { attributes: {} } } })

    const summary = await getDashboardSummary(1)

    expect(summary.activeAlerts).toBe(0)
    expect(summary.totalAlerts).toBe(0)
    expect(summary.recentOpportunities).toEqual([])
    expect(summary.nextChecks).toEqual([])
  })

  it('falls back to flat response when JSON:API envelope is absent', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        attributes: {
          'active-alerts': 2,
          'total-alerts': 4,
          'recent-opportunities': [],
          'next-checks': [],
        },
      },
    })

    const summary = await getDashboardSummary(1)

    expect(summary.activeAlerts).toBe(2)
    expect(summary.totalAlerts).toBe(4)
  })

  it('handles opportunity with null created-at', async () => {
    const oppWithoutDate = { ...OPPORTUNITY_1, 'created-at': null }
    mockGet.mockResolvedValueOnce(
      summaryResponse({
        'active-alerts': 1,
        'total-alerts': 1,
        'recent-opportunities': [oppWithoutDate],
        'next-checks': [],
      }),
    )

    const summary = await getDashboardSummary(1)

    expect(summary.recentOpportunities[0].createdAt).toBeUndefined()
  })
})
