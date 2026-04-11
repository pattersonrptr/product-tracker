import { test, expect } from './fixtures'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/dashboard')
  })

  test('displays the three dashboard cards', async ({
    authenticatedPage: page,
  }) => {
    await expect(page.getByRole('heading', { name: 'Active Alerts' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Recent Opportunities' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Next Checks' })).toBeVisible()
  })

  test('active alerts card shows count', async ({
    authenticatedPage: page,
  }) => {
    const card = page.locator('div').filter({ hasText: /^Active Alerts/ }).first()
    await expect(card).toBeVisible()
    // Should have a "total alert(s) configured" subtext
    await expect(page.getByText(/total alert\(?s?\)? configured/i)).toBeVisible()
  })

  test('clicking active alerts card navigates to alerts page', async ({
    authenticatedPage: page,
  }) => {
    // The Active Alerts card is clickable and navigates to /alerts
    const card = page.locator('[class*="MuiCard"]').filter({ hasText: 'Active Alerts' }).first()
    await card.click()
    await expect(page).toHaveURL(/\/alerts/)
  })
})
