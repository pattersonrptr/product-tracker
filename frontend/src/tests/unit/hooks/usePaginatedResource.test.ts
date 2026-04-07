/**
 * Tests for hooks/usePaginatedResource.ts
 *
 * Uses renderHook from @testing-library/react to run the hook in isolation.
 * The fetcher is a plain vi.fn() that resolves with a PaginatedResult.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { usePaginatedResource } from '@/hooks/usePaginatedResource'
import type { PaginatedResult, PaginationParams } from '@/types/api'

type Item = { id: string; name: string }

function makeFetcher(items: Item[], total = items.length) {
  const resolved: PaginatedResult<Item> = { items, total }
  const fn = vi.fn<(params: PaginationParams) => Promise<PaginatedResult<Item>>>()
  fn.mockResolvedValue(resolved)
  return fn
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('usePaginatedResource', () => {
  it('starts in loading state and then delivers items', async () => {
    const items: Item[] = [
      { id: '1', name: 'Alpha' },
      { id: '2', name: 'Beta' },
    ]
    const fetcher = makeFetcher(items, 2)

    const { result } = renderHook(() => usePaginatedResource(fetcher))

    // Initially loading
    expect(result.current.loading).toBe(true)

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.items).toEqual(items)
    expect(result.current.total).toBe(2)
    expect(result.current.error).toBeNull()
  })

  it('sets error when the fetcher rejects', async () => {
    const fn = vi.fn<(params: PaginationParams) => Promise<PaginatedResult<Item>>>()
    fn.mockRejectedValue(new Error('Server error'))
    const fetcher = fn

    const { result } = renderHook(() => usePaginatedResource(fetcher))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).toBe('Server error')
    expect(result.current.items).toEqual([])
  })

  it('re-fetches when reload() is called', async () => {
    const fetcher = makeFetcher([{ id: '1', name: 'Alpha' }])

    const { result } = renderHook(() => usePaginatedResource(fetcher))
    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(fetcher).toHaveBeenCalledTimes(1)

    act(() => {
      result.current.reload()
    })

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2))
  })

  it('passes the correct limit and offset to the fetcher', async () => {
    const fetcher = makeFetcher([])

    renderHook(() => usePaginatedResource(fetcher, 25))

    await waitFor(() => expect(fetcher).toHaveBeenCalled())

    const params = fetcher.mock.calls[0][0]
    expect(params.limit).toBe(25)
    expect(params.offset).toBe(0)
  })

  it('updates offset when page is changed via setPagination', async () => {
    const fetcher = makeFetcher([])

    const { result } = renderHook(() => usePaginatedResource(fetcher, 10))
    await waitFor(() => expect(result.current.loading).toBe(false))

    act(() => {
      result.current.setPagination({ page: 2, pageSize: 10 })
    })

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2))

    const secondCall = fetcher.mock.calls[1][0]
    expect(secondCall.offset).toBe(20)
    expect(secondCall.limit).toBe(10)
  })
})
