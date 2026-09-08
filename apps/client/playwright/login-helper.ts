import type { Page } from '@playwright/test'
import { expect } from '@playwright/test'

export async function login (page: Page) {
  const username = process.env.VITE_USERNAME_KEYCLOAK
  const password = process.env.VITE_PASSWORD_KEYCLOAK

  if (!username || !password) {
    throw new Error('Variables d\'environnement VITE_USERNAME_KEYCLOAK et VITE_PASSWORD_KEYCLOAK requises pour les tests E2E')
  }

  await page.goto('/')
  await page.fill('input[name="username"]', username)
  await page.fill('input[name="password"]', password)
  await page.click('#kc-login')
  // `toBeVisible()` already retries/auto-waits for the post-login page to
  // settle - a `networkidle` wait ahead of it is redundant and Playwright
  // itself discourages relying on it (background polling/analytics can keep
  // the network "busy" indefinitely).
  await expect(page.getByText('Résumer un texte à partir...')).toBeVisible()
}
