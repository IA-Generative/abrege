import type { IUser } from '@/interfaces/IUser.ts'
import { ABREGE_API_URL } from './constants'

// Le backend est la seule partie de l'app à parler à Keycloak (BFF) : le navigateur ne
// détient aucun jeton, seulement le cookie de session `httpOnly` posé par
// `/api/auth/callback`. `login`/`logout` sont donc des navigations complètes, jamais des
// appels XHR - `login` traverse une redirection vers Keycloak, `logout` doit pouvoir
// clore la session même si le JS de la page courante ne survit pas au retour.

function currentPath (): string {
  return `${window.location.pathname}${window.location.search}${window.location.hash}`
}

export function login (redirectPath?: string): void {
  const redirect = encodeURIComponent(redirectPath ?? currentPath())
  window.location.href = `${ABREGE_API_URL}/auth/login?redirect=${redirect}`
}

export async function logout (): Promise<void> {
  // Ends the local session, then falls back to `/` if the backend response can't be read -
  // clearing the local state must never leave the user stuck on a dead page.
  let redirectUrl = '/'
  try {
    const response = await fetch(`${ABREGE_API_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    })
    const data = await response.json() as { redirectUrl?: string }
    redirectUrl = data.redirectUrl ?? redirectUrl
  } catch (error) {
    console.error('[auth] logout request failed, clearing local state anyway:', error)
  }
  // Redirects through Keycloak's end_session_endpoint (which then redirects back here):
  // the local session cookie alone doesn't end the browser's Keycloak SSO session, so
  // skipping this would sign the user silently back in on the next login.
  window.location.href = redirectUrl
}

export async function fetchMe (): Promise<IUser | null> {
  const response = await fetch(`${ABREGE_API_URL}/auth/me`, {
    credentials: 'include',
  })
  if (!response.ok) {
    return null
  }
  return response.json() as Promise<IUser>
}
