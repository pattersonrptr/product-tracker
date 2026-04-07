/**
 * Tests for services/authService.ts
 *
 * We mock axios directly (authService uses the plain `axios` instance, not
 * the shared apiClient) and stub localStorage to verify the token storage logic.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { login, logout, getStoredToken } from '@/services/authService'

vi.mock('axios')

const mockedAxios = vi.mocked(axios)

const FAKE_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.SIG'

// Minimal localStorage stub
const storage: Record<string, string> = {}
const localStorageMock = {
  getItem: (key: string) => storage[key] ?? null,
  setItem: (key: string, val: string) => { storage[key] = val },
  removeItem: (key: string) => { delete storage[key] },
  clear: () => { Object.keys(storage).forEach((k) => delete storage[k]) },
}

beforeEach(() => {
  vi.stubGlobal('localStorage', localStorageMock)
  localStorageMock.clear()
  vi.resetAllMocks()
})

describe('login', () => {
  it('returns an AuthToken and stores it in localStorage', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({
      data: {
        data: {
          attributes: {
            access_token: FAKE_TOKEN,
            token_type: 'bearer',
            expires_in: 1800,
          },
        },
      },
    })

    const token = await login('user1', 'pass123')

    expect(token.accessToken).toBe(FAKE_TOKEN)
    expect(token.tokenType).toBe('bearer')
    expect(token.expiresIn).toBe(1800)
    expect(localStorage.getItem('token')).toBe(FAKE_TOKEN)
  })

  it('falls back to flat response when JSON:API envelope is absent', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({
      data: {
        access_token: FAKE_TOKEN,
        token_type: 'bearer',
        expires_in: 3600,
      },
    })

    const token = await login('user1', 'pass123')
    expect(token.accessToken).toBe(FAKE_TOKEN)
  })

  it('propagates errors thrown by axios', async () => {
    mockedAxios.post = vi.fn().mockRejectedValue(new Error('Network error'))
    await expect(login('user1', 'bad')).rejects.toThrow('Network error')
  })
})

describe('logout', () => {
  it('removes the token from localStorage', () => {
    localStorage.setItem('token', FAKE_TOKEN)
    logout()
    expect(localStorage.getItem('token')).toBeNull()
  })
})

describe('getStoredToken', () => {
  it('returns null when no token is stored', () => {
    expect(getStoredToken()).toBeNull()
  })

  it('returns the stored token string', () => {
    localStorage.setItem('token', FAKE_TOKEN)
    expect(getStoredToken()).toBe(FAKE_TOKEN)
  })
})
