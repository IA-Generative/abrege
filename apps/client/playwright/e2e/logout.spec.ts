import { expect, test } from '@playwright/test'
import { login } from '../login-helper'

test.describe('Logout with Keycloak', () => {
  test('should logout successfully', async ({ page }) => {
    await login(page)

    const logoutLink = page.getByText(/se déconnecter/i)
    await expect(logoutLink).toBeVisible({ timeout: 60000 })
    await logoutLink.click()

    await page.waitForTimeout(2000)

    await expect(page.getByText('Connectez-vous à votre compte')).toBeVisible()
  })
})
