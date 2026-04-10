/**
 * Tests for services/priceAlertService.ts
 *
 * Mocks apiClient and validates that the service correctly serializes
 * and deserializes price alert data.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { getPriceAlerts, getPriceAlertsByUser, createPriceAlert, deletePriceAlert } from '@/services/priceAlertService'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { apiClient } from '@/api/client'

const mockedClient = vi.mocked(apiClient)

const RAW_ALERT = {
  search_term: 'iPhone 15',
  max_price: 799.99,
  is_active: true,
  frequency_minutes: 60,
  last_triggered_at: undefined,
  user_id: 1,
  search_config_id: undefined,
  source_website_ids: [1, 2],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const JSONAPI_SINGLE = {
  data: {
    id: '42',
    type: 'price-alerts',
    attributes: RAW_ALERT,
  },
}

const JSONAPI_COLLECTION = {
  data: [{ id: '42', type: 'price-alerts', attributes: RAW_ALERT }],
  meta: { total: 1 },
}

beforeEach(() => {
  vi.resetAllMocks()
})

describe('getPriceAlerts', () => {
  it('fetches and maps a paginated list of alerts', async () => {
    mockedClient.get = vi.fn().mockResolvedValue({ data: JSONAPI_COLLECTION })

    const result = await getPriceAlerts({ limit: 10, offset: 0 })

    expect(result.total).toBe(1)
    expect(result.items).toHaveLength(1)
    const alert = result.items[0]
    expect(alert.id).toBe('42')
    expect(alert.searchTerm).toBe('iPhone 15')
    expect(alert.maxPrice).toBe(799.99)
    expect(alert.isActive).toBe(true)
    expect(alert.sourceWebsiteIds).toEqual([1, 2])
  })
})

describe('getPriceAlertsByUser', () => {
  it('fetches alerts for a specific user', async () => {
    mockedClient.get = vi.fn().mockResolvedValue({ data: JSONAPI_COLLECTION })

    const alerts = await getPriceAlertsByUser(1)

    expect(alerts).toHaveLength(1)
    expect(alerts[0].userId).toBe(1)
  })
})

describe('createPriceAlert', () => {
  it('posts JSON:API body and returns mapped alert', async () => {
    mockedClient.post = vi.fn().mockResolvedValue({ data: JSONAPI_SINGLE })

    const alert = await createPriceAlert({
      searchTerm: 'iPhone 15',
      maxPrice: 799.99,
      userId: 1,
      sourceWebsiteIds: [1, 2],
    })

    expect(mockedClient.post).toHaveBeenCalledOnce()
    const [, body] = (mockedClient.post as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(body.data.attributes.search_term).toBe('iPhone 15')
    expect(body.data.attributes.max_price).toBe(799.99)
    expect(alert.searchTerm).toBe('iPhone 15')
  })
})

describe('deletePriceAlert', () => {
  it('calls DELETE on the correct endpoint', async () => {
    mockedClient.delete = vi.fn().mockResolvedValue({})

    await deletePriceAlert('42')

    expect(mockedClient.delete).toHaveBeenCalledOnce()
    expect((mockedClient.delete as ReturnType<typeof vi.fn>).mock.calls[0][0]).toContain('/42')
  })
})
