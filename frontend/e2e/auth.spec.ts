import { test, expect, login, ADMIN_USER } from './fixtures'

test.describe('Login', () => {
  test('shows the login form', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('Product Tracker')).toBeVisible()
    await expect(page.getByLabel('Username')).toBeVisible()
    await expect(page.getByRole('textbox', { name: 'Password' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible()
  })

  test('redirects to dashboard after successful login', async ({ page }) => {
    await login(page)
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('wrong_user')
    await page.getByRole('textbox', { name: 'Password' }).fill('wrong_pass')
    await page.getByRole('button', { name: 'Sign In' }).click()
    await expect(page.getByText(/invalid username or password/i)).toBeVisible({
      timeout: 5000,
    })
  })

  test('shows validation message when fields are empty', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: 'Sign In' }).click()
    await expect(
      page.getByText(/please enter username and password/i),
    ).toBeVisible()
  })

  test('navigates to register page', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/register/)
  })
})

test.describe('Logout', () => {
  test('logs out and redirects to login', async ({ authenticatedPage: page }) => {
    await page.getByRole('button', { name: /logout/i }).click()
    // Confirmation dialog appears
    await page.getByRole('button', { name: 'Sign out' }).click()
    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('Register', () => {
  test('shows the registration form', async ({ page }) => {
    await page.goto('/register')
    await expect(page.getByRole('heading', { name: 'Create Account' })).toBeVisible()
    await expect(page.getByLabel('Username')).toBeVisible()
    await expect(page.getByLabel('Email')).toBeVisible()
    await expect(page.getByRole('textbox', { name: 'Password', exact: true })).toBeVisible()
    await expect(page.getByLabel('Confirm Password')).toBeVisible()
  })

  test('shows error when passwords do not match', async ({ page }) => {
    await page.goto('/register')
    await page.getByLabel('Username').fill('testuser_pw_mismatch')
    await page.getByLabel('Email').fill('test@example.com')
    await page.getByRole('textbox', { name: 'Password', exact: true }).fill('password123')
    await page.getByLabel('Confirm Password').fill('different123')
    await page.getByRole('button', { name: 'Create Account' }).click()
    await expect(page.getByText(/passwords do not match/i).first()).toBeVisible()
  })

  test('registers a new user and redirects to login', async ({ page }) => {
    const unique = `e2e_user_${Date.now()}`
    await page.goto('/register')
    await page.getByLabel('Username').fill(unique)
    await page.getByLabel('Email').fill(`${unique}@test.com`)
    await page.getByRole('textbox', { name: 'Password', exact: true }).fill('TestPass123!')
    await page.getByLabel('Confirm Password').fill('TestPass123!')
    await page.getByRole('button', { name: 'Create Account' }).click()
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 })
  })
})

test.describe('Auth guard', () => {
  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })

  test('authenticated user accessing /login is redirected to dashboard', async ({
    page,
  }) => {
    await login(page)
    await page.goto('/login')
    await expect(page).toHaveURL(/\/dashboard/)
  })
})
