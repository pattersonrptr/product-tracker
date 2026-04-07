/**
 * Tests for lib/logger.ts
 *
 * Strategy: spy on console methods to verify the logger routes to the right
 * console function and that the formatted string includes the expected parts.
 * We do NOT test `import.meta.env.PROD` branching here (that is a build-time
 * value); instead we verify the public API contract.
 */

import { describe, expect, it, vi, afterEach } from 'vitest'
import { logger } from '@/lib/logger'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('logger.debug', () => {
  it('calls console.debug', () => {
    const spy = vi.spyOn(console, 'debug').mockImplementation(() => {})
    logger.debug('test debug message')
    expect(spy).toHaveBeenCalledOnce()
  })

  it('includes the message in the output', () => {
    const spy = vi.spyOn(console, 'debug').mockImplementation(() => {})
    logger.debug('hello debug')
    const firstArg = spy.mock.calls[0][0] as string
    expect(firstArg).toContain('hello debug')
    expect(firstArg).toContain('[DEBUG]')
  })

  it('passes context as a second argument when provided', () => {
    const spy = vi.spyOn(console, 'debug').mockImplementation(() => {})
    logger.debug('with context', { key: 'value' })
    expect(spy.mock.calls[0][1]).toEqual({ key: 'value' })
  })
})

describe('logger.info', () => {
  it('calls console.info', () => {
    const spy = vi.spyOn(console, 'info').mockImplementation(() => {})
    logger.info('test info')
    expect(spy).toHaveBeenCalledOnce()
  })

  it('includes [INFO] in the formatted message', () => {
    const spy = vi.spyOn(console, 'info').mockImplementation(() => {})
    logger.info('info message')
    expect(spy.mock.calls[0][0]).toContain('[INFO]')
  })
})

describe('logger.warn', () => {
  it('calls console.warn', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.warn('test warn')
    expect(spy).toHaveBeenCalledOnce()
  })

  it('passes an error object as a second argument when context is empty', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const err = new Error('something went wrong')
    logger.warn('warn with error', {}, err)
    // Empty context is stripped → error shifts to index [1]
    expect(spy.mock.calls[0][1]).toBe(err)
  })

  it('passes error at index [2] when context is non-empty', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const err = new Error('something went wrong')
    logger.warn('warn with error', { code: 42 }, err)
    expect(spy.mock.calls[0][1]).toEqual({ code: 42 })
    expect(spy.mock.calls[0][2]).toBe(err)
  })
})

describe('logger.error', () => {
  it('calls console.error', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('test error')
    expect(spy).toHaveBeenCalledOnce()
  })

  it('includes [ERROR] and the message', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('something failed', { code: 500 })
    const firstArg = spy.mock.calls[0][0] as string
    expect(firstArg).toContain('[ERROR]')
    expect(firstArg).toContain('something failed')
  })

  it('does not append context argument when context is empty', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('no context', {})
    // Only the formatted string; no second arg when context is empty
    expect(spy.mock.calls[0]).toHaveLength(1)
  })
})
