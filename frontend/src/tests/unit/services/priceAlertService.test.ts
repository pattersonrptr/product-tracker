/**
 * Tests for services/priceAlertService.ts
 *
 * We mock the shared apiClient (used by all resource services) and verify
 * that every service function hits the correct endpoint, transforms the
 * JSON:API response into typed domain objects, and forwards errors.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import {
  getPriceAlerts,
  getPriceAlertsByUser,
  getPriceAlertById,
  createPriceAlert,
  updatePriceAlert,
  deletePriceAlert,
} from '@/services/priceAlertService'
import type {
  PriceAlertCreatePayload,
  PriceAlertUpdatePayload,
} from '@/types/priceAlert'

// ---------- mocks ----------

const { mockGet, mockPost, mockPut, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDelete: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  },
}))

vi.mock('@/lib/logger', () => ({
  logger: { debug: vi.fn(), warn: vi.fn(), error: vi.fn() },
}))

// ---------- helpers ----------

/** Build a JSON:API single-resource response */
function singleResponse(id: string, attrs: Record<string, unknown>) {
  return { data: { data: { id, type: 'price-alerts', attributes: attrs } } }
}

/** Build a JSON:API collection response */
function collectionResponse(
  items: { id: string; attrs: Record<string, unknown> }[],
  total?: number,
) {
  return {
    data: {
      data: items.map((i) => ({
        id: i.id,
        type: 'price-alerts',
        attributes: i.attrs,
      })),
      meta: { total: total ?? items.length },
    },
  }
}

const RAW_ATTRS = {
  search_term: 'iPhone 15',
  max_price: 4500,
  is_active: true,
  frequency_minutes: 60,
  last_triggered_at: '2025-01-15T10:00:00Z',
  user_id: 1,
  search_config_id: null,
  source_website_ids: [1, 2],
  created_at: '2025-01-10T08:00:00Z',
  updated_at: '2025-01-15T10:00:00Z',
}

beforeEach(() => {
  vi.resetAllMocks()
})

// ---------- getPriceAlerts ----------

describe('getPriceAlerts', () => {
  it('returns a paginated result with camelCase objects', async () => {
    mockGet.mockResolvedValue(
      collectionResponse([{ id: '1', attrs: RAW_ATTRS }], 1),
    )

    const result = await getPriceAlerts({ limit: 10, offset: 0 })

    expect(mockGet).toHaveBeenCalledOnce()
    expect(result.total).toBe(1)
    expect(result.items).toHaveLength(1)

    const alert = result.items[0]
    expect(alert.id).toBe('1')
    expect(alert.searchTerm).toBe('iPhone 15')
    expect(alert.maxPrice).toBe(4500)
    expect(alert.isActive).toBe(true)
    expect(alert.frequencyMinutes).toBe(60)
    expect(alert.sourceWebsiteIds).toEqual([1, 2])
  })

  it('forwards pagination params to apiClient', async () => {
    mockGet.mockResolvedValue(collectionResponse([], 0))

    await getPriceAlerts({ limit: 25, offset: 50 })

    expect(mockGet).toHaveBeenCalledWith(
      expect.any(String),
      { params: { limit: 25, offset: 50 } },
    )
  })

  it('propagates API errors', async () => {
    mockGet.mockRejectedValue(new Error('Server down'))
    await expect(getPriceAlerts({ limit: 10, offset: 0 })).rejects.toThrow(
      'Server down',
    )
  })
})

// ---------- getPriceAlertsByUser ----------

describe('getPriceAlertsByUser', () => {
  it('calls the user-scoped endpoint and returns alerts', async () => {
    mockGet.mockResolvedValue(
      collectionResponse([{ id: '5', attrs: RAW_ATTRS }], 1),
    )

    const alerts = await getPriceAlertsByUser(42)

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('/user/42'),
    )
    expect(alerts).toHaveLength(1)
    expect(alerts[0].id).toBe('5')
    expect(alerts[0].searchTerm).toBe('iPhone 15')
  })

  it('returns an empty array when user has no alerts', async () => {
    mockGet.mockResolvedValue(collectionResponse([], 0))

    const alerts = await getPriceAlertsByUser(99)
    expect(alerts).toEqual([])
  })
})

// ---------- getPriceAlertById ----------

describe('getPriceAlertById', () => {
  it('returns a single typed PriceAlert', async () => {
    mockGet.mockResolvedValue(singleResponse('7', RAW_ATTRS))

    const alert = await getPriceAlertById('7')

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('/price-alerts/7'),
    )
    expect(alert.id).toBe('7')
    expect(alert.userId).toBe(1)
    expect(alert.lastTriggeredAt).toBe('2025-01-15T10:00:00Z')
  })

  it('propagates 404 errors', async () => {
    mockGet.mockRejectedValue(new Error('Not found'))
    await expect(getPriceAlertById('999')).rejects.toThrow('Not found')
  })
})

// ---------- createPriceAlert ----------

describe('createPriceAlert', () => {
  it('posts a JSON:API wrapped payload and returns the created alert', async () => {
    const payload: PriceAlertCreatePayload = {
      searchTerm: 'Galaxy S24',
      maxPrice: 3000,
      isActive: true,
      frequencyMinutes: 120,
      sourceWebsiteIds: [3],
      userId: 1,
    }

    const created = {
      ...RAW_ATTRS,
      search_term: 'Galaxy S24',
      max_price: 3000,
      frequency_minutes: 120,
      source_website_ids: [3],
    }

    mockPost.mockResolvedValue(singleResponse('10', created))

    const result = await createPriceAlert(payload)

    expect(mockPost).toHaveBeenCalledOnce()
    // Verify the body is JSON:API wrapped with snake_case attributes
    const body = mockPost.mock.calls[0][1] as Record<string, unknown>
    const data = body.data as Record<string, unknown>
    expect(data.type).toBe('price-alerts')
    expect(data.attributes).toEqual(
      expect.objectContaining({
        search_term: 'Galaxy S24',
        max_price: 3000,
        is_active: true,
        frequency_minutes: 120,
        source_website_ids: [3],
        user_id: 1,
      }),
    )

    expect(result.id).toBe('10')
    expect(result.searchTerm).toBe('Galaxy S24')
    expect(result.maxPrice).toBe(3000)
  })
})

// ---------- updatePriceAlert ----------

describe('updatePriceAlert', () => {
  it('puts a JSON:API wrapped payload with id and returns the updated alert', async () => {
    const payload: PriceAlertUpdatePayload = {
      maxPrice: 4000,
      isActive: false,
    }

    const updated = { ...RAW_ATTRS, max_price: 4000, is_active: false }

    mockPut.mockResolvedValue(singleResponse('7', updated))

    const result = await updatePriceAlert('7', payload)

    expect(mockPut).toHaveBeenCalledWith(
      expect.stringContaining('/price-alerts/7'),
      expect.objectContaining({
        data: expect.objectContaining({
          type: 'price-alerts',
          id: '7',
          attributes: expect.objectContaining({
            max_price: 4000,
            is_active: false,
          }),
        }),
      }),
    )

    expect(result.id).toBe('7')
    expect(result.maxPrice).toBe(4000)
    expect(result.isActive).toBe(false)
  })

  it('only includes provided fields in the payload', async () => {
    const payload: PriceAlertUpdatePayload = { isActive: true }

    mockPut.mockResolvedValue(singleResponse('3', RAW_ATTRS))

    await updatePriceAlert('3', payload)

    const body = mockPut.mock.calls[0][1] as Record<string, unknown>
    const attrs = (body.data as Record<string, unknown>).attributes as Record<
      string,
      unknown
    >
    expect(attrs).toEqual({ is_active: true })
    expect(attrs).not.toHaveProperty('search_term')
    expect(attrs).not.toHaveProperty('max_price')
  })
})

// ---------- deletePriceAlert ----------

describe('deletePriceAlert', () => {
  it('calls delete on the correct endpoint', async () => {
    mockDelete.mockResolvedValue({ data: null })

    await deletePriceAlert('12')

    expect(mockDelete).toHaveBeenCalledWith(
      expect.stringContaining('/price-alerts/12'),
    )
  })

  it('propagates errors', async () => {
    mockDelete.mockRejectedValue(new Error('Forbidden'))
    await expect(deletePriceAlert('12')).rejects.toThrow('Forbidden')
  })
})
