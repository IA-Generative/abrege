import process from 'node:process'
import { expect, type Page } from '@playwright/test'

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
  await page.waitForLoadState('networkidle')
  await expect(page.getByText('Résumer un texte à partir...')).toBeVisible()
}
