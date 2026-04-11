/**
 * Shared Playwright fixtures for E2E tests.
 *
 * Provides:
 * - `authenticatedPage` — a Page already logged in as the default admin user
 * - `adminCredentials` — username/password for the admin user
 * - `login` helper — logs in programmatically via the UI
 */

import { test as base, expect, type Page, request } from '@playwright/test'

export const ADMIN_USER = {
  username: 'admin',
  password: 'admin',
}

const API_BASE = process.env.E2E_API_URL ?? 'http://localhost:8000'

/** Get an API auth token. */
async function getAuthToken(
  username = ADMIN_USER.username,
  password = ADMIN_USER.password,
): Promise<string> {
  const ctx = await request.newContext()
  const resp = await ctx.post(`${API_BASE}/auth/login`, {
    form: { username, password, grant_type: 'password' },
  })
  const body = await resp.json()
  await ctx.dispose()
  return body.data.attributes.access_token as string
}

/** Create a disposable auth context for API calls. */
async function apiContext() {
  const token = await getAuthToken()
  return request.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${token}` },
  })
}

/** Delete all price alerts whose keyword starts with a given prefix. */
export async function cleanupTestAlerts(prefix = 'e'): Promise<void> {
  const ctx = await apiContext()
  const resp = await ctx.get(`${API_BASE}/price-alerts/`, {
    params: { 'page[size]': '100' },
  })
  const body = await resp.json()
  const alerts = body?.data ?? []
  for (const alert of alerts) {
    const searchTerm: string = alert.attributes?.search_term ?? ''
    if (searchTerm.startsWith(prefix)) {
      await ctx.delete(`${API_BASE}/price-alerts/${alert.id}`)
    }
  }
  await ctx.dispose()
}

/** Delete all source websites whose name starts with a given prefix. */
export async function cleanupTestWebsites(prefix = 'e2e-'): Promise<void> {
  const ctx = await apiContext()
  const resp = await ctx.get(`${API_BASE}/source-websites/`, {
    params: { limit: '100', offset: '0' },
  })
  const body = await resp.json()
  const items = body?.data ?? []
  for (const item of items) {
    const name: string = item.attributes?.name ?? ''
    if (name.startsWith(prefix)) {
      await ctx.delete(`${API_BASE}/source-websites/${item.id}`)
    }
  }
  await ctx.dispose()
}

/** Delete all search configs whose search_term starts with a given prefix. */
export async function cleanupTestConfigs(prefix = 'e2e-'): Promise<void> {
  const ctx = await apiContext()
  const resp = await ctx.get(`${API_BASE}/search-configs/`, {
    params: { limit: '100', offset: '0' },
  })
  const body = await resp.json()
  const items = body?.data ?? []
  for (const item of items) {
    const term: string = item.attributes?.search_term ?? ''
    if (term.startsWith(prefix)) {
      await ctx.delete(`${API_BASE}/search-configs/${item.id}`)
    }
  }
  await ctx.dispose()
}

/** Log in via the Login page UI. */
export async function login(
  page: Page,
  username = ADMIN_USER.username,
  password = ADMIN_USER.password,
): Promise<void> {
  await page.goto('/login')
  await page.getByLabel('Username').fill(username)
  await page.getByRole('textbox', { name: 'Password' }).fill(password)
  await page.getByRole('button', { name: 'Sign In' }).click()
  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 })
}

/**
 * Extended test fixtures.
 *
 * `authenticatedPage` provides a Page that is already logged in.
 */
export const test = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ page }, use) => {
    await login(page)
    await use(page)
  },
})

export { expect }
