import { expect, type Page } from '@playwright/test'

export async function login (page: Page) {
  await page.goto('/')
  await page.fill('input[name="username"]', 'test@gouv.fr')
  await page.fill('input[name="password"]', 'qJ"jZ>>_:B5u$BG')
  await page.click('#kc-login')
  await page.waitForLoadState('networkidle')
  await expect(page.getByText('Résumer un texte à partir...')).toBeVisible()
}
