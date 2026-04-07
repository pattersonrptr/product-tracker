/**
 * Tests for the JSON:API parsers in api/jsonapi.ts
 */

import { describe, expect, it } from 'vitest'
import { unwrapCollection, unwrapSingle, wrapPayload } from '@/api/jsonapi'

describe('unwrapSingle', () => {
  it('extracts attributes and merges id', () => {
    const response = {
      data: {
        id: '42',
        type: 'products',
        attributes: { title: 'Test Product', current_price: 99.9 },
      },
    }
    const result = unwrapSingle(response)
    expect(result).toEqual({ id: '42', title: 'Test Product', current_price: 99.9 })
  })

  it('handles missing id gracefully', () => {
    const response = {
      data: {
        id: null,
        type: 'products',
        attributes: { title: 'No ID' },
      },
    }
    const result = unwrapSingle(response as unknown as Parameters<typeof unwrapSingle>[0])
    expect(result.id).toBe('')
  })
})

describe('unwrapCollection', () => {
  it('extracts all items with ids and total from meta', () => {
    const response = {
      data: [
        { id: '1', type: 'products', attributes: { title: 'A' } },
        { id: '2', type: 'products', attributes: { title: 'B' } },
      ],
      meta: { total: 50 },
    }
    const result = unwrapCollection(response)
    expect(result.total).toBe(50)
    expect(result.items).toHaveLength(2)
    expect(result.items[0]).toEqual({ id: '1', title: 'A' })
    expect(result.items[1]).toEqual({ id: '2', title: 'B' })
  })

  it('falls back to items.length when meta.total is absent', () => {
    const response = {
      data: [{ id: '1', type: 'x', attributes: { name: 'test' } }],
    }
    const result = unwrapCollection(response)
    expect(result.total).toBe(1)
  })
})

describe('wrapPayload', () => {
  it('wraps attributes without id for POST', () => {
    const body = wrapPayload('products', { title: 'New' })
    expect(body).toEqual({
      data: { type: 'products', attributes: { title: 'New' } },
    })
    expect('id' in body.data).toBe(false)
  })

  it('includes id for PATCH', () => {
    const body = wrapPayload('products', { title: 'Updated' }, '7')
    expect(body.data.id).toBe('7')
  })
})
