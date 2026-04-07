/**
 * Axios HTTP client with:
 *   - JWT bearer token injected on every request
 *   - Proactive token refresh when expiry is within 15 minutes
 *   - 401 response interception with single in-flight refresh + queue
 *   - Session expiry callbacks for the AuthContext to react to
 */

import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'
import { jwtDecode } from 'jwt-decode'
import { API_BASE_URL, ENDPOINTS } from './endpoints'
import { logger } from '@/lib/logger'
import type { JwtPayload } from '@/types/auth'

// ---------------------------------------------------------------------------
// Session callbacks — set by AuthContext on mount
// ---------------------------------------------------------------------------

type Callback = () => void
type MessageCallback = (message: string) => void

let onSessionExpired: MessageCallback | null = null
let onTokenUpdated: Callback | null = null

export function setOnSessionExpired(cb: MessageCallback): void {
  onSessionExpired = cb
}
export function setOnTokenUpdated(cb: Callback): void {
  onTokenUpdated = cb
}

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

const REFRESH_THRESHOLD_MS = 15 * 60 * 1000 // 15 minutes

function getToken(): string | null {
  return localStorage.getItem('token')
}

function isTokenNearExpiry(token: string): boolean {
  try {
    const { exp } = jwtDecode<JwtPayload>(token)
    return exp * 1000 - Date.now() < REFRESH_THRESHOLD_MS
  } catch {
    return true
  }
}

// ---------------------------------------------------------------------------
// Refresh token logic (single in-flight + queue)
// ---------------------------------------------------------------------------

let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function flushQueue(token: string | null, error: unknown = null): void {
  pendingQueue.forEach((p) => (token ? p.resolve(token) : p.reject(error)))
  pendingQueue = []
}

async function refreshAccessToken(): Promise<string> {
  if (isRefreshing) {
    return new Promise<string>((resolve, reject) =>
      pendingQueue.push({ resolve, reject }),
    )
  }

  isRefreshing = true
  logger.debug('Refreshing access token')

  try {
    const currentToken = getToken()
    if (!currentToken) throw new Error('No token available for refresh')

    const response = await axios.post(
      ENDPOINTS.auth.refresh,
      {},
      { headers: { Authorization: `Bearer ${currentToken}` } },
    )

    // Backend returns JSON:API: { data: { attributes: { access_token } } }
    const newToken: string =
      response.data?.data?.attributes?.access_token ??
      response.data?.access_token

    if (!newToken) throw new Error('Refresh response did not contain a token')

    localStorage.setItem('token', newToken)
    onTokenUpdated?.()
    flushQueue(newToken)
    logger.info('Access token refreshed successfully')
    return newToken
  } catch (err) {
    flushQueue(null, err)
    logger.error('Token refresh failed', {}, err)
    const token = getToken()
    if (token) {
      localStorage.removeItem('token')
      onSessionExpired?.('Your session has expired. Please log in again.')
    }
    throw err
  } finally {
    isRefreshing = false
  }
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach token, proactively refresh if near expiry
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (!token) return config

    if (isTokenNearExpiry(token)) {
      logger.debug('Token near expiry, refreshing before request')
      try {
        const fresh = await refreshAccessToken()
        config.headers.Authorization = `Bearer ${fresh}`
        return config
      } catch {
        return Promise.reject(new Error('Could not refresh token'))
      }
    }

    config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor — handle 401 with refresh + retry
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean
    }

    const status = error.response?.status
    const isRefreshEndpoint = original.url === ENDPOINTS.auth.refresh

    if (status === 401 && !original._retried && !isRefreshEndpoint) {
      original._retried = true
      try {
        const fresh = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${fresh}`
        return apiClient(original)
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)
