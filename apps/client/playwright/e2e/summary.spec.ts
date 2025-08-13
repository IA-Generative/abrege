import { expect, test } from '@playwright/test'
import { login } from '../login-helper'

test.describe('Summary text with Text or URL', () => {
  test('should display summary for text input', async ({ page }) => {
    await login(page)

    await page.getByRole('tab', { name: 'd\'un texte copié/collé' }).click()

    const textToSummarize = 'Le ministère de l\'Intérieur est le ministère du gouvernement français chargé traditionnellement de la sécurité intérieure, de l\'administration du territoire et des libertés publiques. Depuis sa création, le ministère de l\'Intérieur est au cœur de l\'administration française : il assure sur tout le territoire le maintien et la cohésion des institutions du pays. Son organisation, ses moyens humains et matériels constituent l\'outil privilégié de l\'État pour garantir aux citoyens l\'exercice des droits, devoirs et libertés réaffirmés par la Constitution de la Ve République.\n\nInstallé à l\'hôtel de Beauvau, dans le 8e arrondissement de Paris, à quelques pas du palais de l\'Élysée, il est surnommé, par métonymie, la Place Beauvau.\n\nL\'actuel ministre de l\'Intérieur est Bruno Retailleau, qui assure la fonction depuis le 21 septembre 2024.'
    await page.getByLabel('Copier/coller un texte').fill(textToSummarize)

    await page.getByRole('button', { name: 'Générer' }).click()
    await page.waitForTimeout(15000)
    await expect(page.locator('p', { hasText: 'Retailleau' })).toBeVisible()
    await expect(page.locator('p', { hasText: '21 septembre 2024' })).toBeVisible()
  })

  test('should display summary for URL input', async ({ page }) => {
    await login(page)

    await page.getByRole('tab', { name: 'd\'une URL' }).click()
    await page.getByLabel('Entrer une url').fill('https://fr.wikipedia.org/wiki/Minist%C3%A8re_de_l%27Int%C3%A9rieur_(France)')
    await page.getByRole('button', { name: 'Générer' }).click()
    await page.waitForTimeout(15000)
    await expect(page.getByText('Direction générale de la Police nationale')).toBeVisible()
    await expect(page.getByText('Hôtel de Beauvau')).toBeVisible()
  })
})
