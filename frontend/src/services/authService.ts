/**
 * Authentication service.
 * Handles login, logout and token storage.
 */

import axios from 'axios'
import { ENDPOINTS } from '@/api/endpoints'
import { logger } from '@/lib/logger'
import type { AuthToken } from '@/types/auth'

/** Raw JSON:API attributes returned by POST /auth/login */
interface RawTokenAttributes {
  access_token: string
  token_type: string
  expires_in: number
}

/**
 * Authenticate with username + password.
 * Stores the token in localStorage and returns the parsed AuthToken.
 */
export async function login(
  username: string,
  password: string,
): Promise<AuthToken> {
  logger.info('Attempting login', { username })

  const response = await axios.post(
    ENDPOINTS.auth.login,
    new URLSearchParams({ username, password, grant_type: 'password' }),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  )

  // JSON:API envelope: { data: { attributes: { access_token, ... } } }
  const attrs: RawTokenAttributes =
    response.data?.data?.attributes ?? response.data

  const token: AuthToken = {
    accessToken: attrs.access_token,
    tokenType: attrs.token_type,
    expiresIn: attrs.expires_in,
  }

  localStorage.setItem('token', token.accessToken)
  logger.info('Login successful', { username })
  return token
}

/** Remove the stored token (client-side logout). */
export function logout(): void {
  localStorage.removeItem('token')
  logger.info('User logged out')
}

/** Returns the raw JWT string or null if not authenticated. */
export function getStoredToken(): string | null {
  return localStorage.getItem('token')
}
